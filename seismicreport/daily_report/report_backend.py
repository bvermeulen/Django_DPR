import typing
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from django.db.utils import IntegrityError
from django.db.models import Q
from daily_report.models.daily_models import (
    Daily, SourceProduction, ReceiverProduction, TimeBreakdown, HseWeather, ToolBox,
)
from daily_report.models.project_models import Project, Block
import daily_report.receiver_backend as _receiver_backend
import daily_report.hseweather_backend as  _hse_backend
import daily_report.graph_backend as _graph_backend
from seismicreport.vars import (
    TCF_table, BGP_DR_table, source_prod_schema, time_breakdown_schema, ops_time_keys,
    standby_keys, downtime_keys, NAME_LENGTH, DESCR_LENGTH, COMMENT_LENGTH, NO_DATE_STR,
    WEEKDAYS, CTM_METHOD
)
from seismicreport.utils.plogger import Logger
from seismicreport.utils.utils_funcs import (
    calc_ratio, nan_array, get_sourcereceivertype_names
)

logger = Logger.getlogger()

class ReportInterface(_receiver_backend.Mixin, _hse_backend.Mixin, _graph_backend.Mixin):

    def __init__(self, media_dir):
        self.media_dir = Path(media_dir)
        self.prod_series = None
        self.time_series = None
        self.hse_series = None
        self.mpr_rec_hours = 24.0

    @staticmethod
    def get_value(day_df, kw):
        if kw not in BGP_DR_table:
            return np.nan

        r, c = BGP_DR_table[kw]
        try:
            return day_df.iat[r, c]

        except IndexError:
            return np.nan

    @staticmethod
    def get_project(project_name):
        try:
            project = Project.objects.get(project_name=project_name)

        except Project.DoesNotExist:
            project = None

        return project

    def get_latest_report_id(self, project_name):
        project = self.get_project(project_name)
        daily = project.dailies.all().order_by(
            'production_date').last() if project else None
        if daily:
            return daily.id, daily.production_date

        else:
            return 0, None

    def calc_ctm(self, daily, sourcetype_name, tcf):
        if not daily or np.isnan(tcf):
            return np.nan

        sourcetype_obj = daily.project.sourcetypes.get(sourcetype_name=sourcetype_name)
        mpr_vibes = sourcetype_obj.mpr_vibes
        mpr_sweep = sourcetype_obj.mpr_sweep_length
        mpr_moveup = sourcetype_obj.mpr_moveup
        # need mpr_rec_hours for graph_backend
        #TODO self.mpr_rec_hours - fix this ugly patch!
        self.mpr_rec_hours = sourcetype_obj.mpr_rec_hours
        if not isinstance(self.mpr_rec_hours, float):
            self.mpr_rec_hours = 24.0

        if mpr_vibes == 0 or mpr_sweep == 0 or mpr_moveup == 0:
            return np.nan

        ctm = int(3600 / (mpr_sweep + mpr_moveup) * mpr_vibes * tcf * self.mpr_rec_hours)

        return ctm

    def calc_ctm_series(self, daily, sourcetype_name, tcf_series):
        ctm_series = []
        for tcf in tcf_series:
            ctm_series.append(self.calc_ctm(daily, sourcetype_name, tcf))

        return np.array(ctm_series)

    @staticmethod
    def calc_rate(daily, ctm_method, app_ctm, total_time, standby_time):
        ''' IMH opinion correct calculation of the rate
        '''

        if ctm_method == 'Legacy':
            standby_rate = daily.project.standby_rate
            cap_rate = daily.project.cap_rate
            cap_app_ctm = daily.project.cap_app_ctm
            if app_ctm > 1 and cap_app_ctm > 1 and cap_rate > 1:
                app_ctm = 1 + (cap_rate - 1) * min((app_ctm - 1) / (cap_app_ctm - 1), 1)

            return (app_ctm * total_time + standby_rate * standby_time) / total_time

        else:

            standby_rate = daily.project.standby_rate
            cap_rate = daily.project.cap_rate
            cap_app_ctm = daily.project.cap_app_ctm
            if app_ctm > 1 and cap_app_ctm > 1 and cap_rate > 1:
                app_ctm = 1 + (cap_rate - 1) * min((app_ctm - 1) / (cap_app_ctm - 1), 1)

            return (
                (app_ctm * (total_time - standby_time) + standby_rate * standby_time) /
                total_time
            )

    def save_report_file(self, project, report_file) -> datetime:
        report_date = self.populate_report(project, report_file.temporary_file_path())
        report_file.close()

        return report_date

    @staticmethod
    def load_report_db(project, report_date):
        return_empty = (None, {})

        try:
            day = Daily.objects.get(
                production_date=report_date,
                project=project)

        except Daily.DoesNotExist:
            return return_empty

        if day.block:
            block_name = day.block.block_name

        else:
            block_name = ''

        day_initial = {
            'id': day.id,
            'production_date': day.production_date,
            'project_name': day.project.project_name,
            'block_name': block_name,
            'csr_comment': day.csr_comment,
            'pm_comment': day.pm_comment,
            'staff': [person.id for person in day.staff.all()]
        }

        return day, day_initial

    def populate_report(self, project, daily_report_file) -> datetime:
        ''' populates db with values from the daily report file
            daily report file is an excel file with fields according
            the BGP_DR_table
        '''
        day_df = pd.read_excel(daily_report_file, header=None)
        if project.project_name != self.get_value(day_df, 'project'):
            return None

        # create/ update day values
        try:
            day = Daily.objects.create(
                production_date=self.get_value(day_df, 'date'),
                project=project)

        except IntegrityError:
            day = Daily.objects.get(
                production_date=self.get_value(day_df, 'date'),
                project=project)

        sourcetype_name, receivertype_name = get_sourcereceivertype_names(day)

        if not project.sourcetypes.filter(
                sourcetype_name=sourcetype_name[:NAME_LENGTH]):
            return None

        if not project.receivertypes.filter(
                receivertype_name=receivertype_name[:NAME_LENGTH]):
            return None

        day.pm_comment = (
            '\n'.join([str(self.get_value(day_df, f'comment {i}')) for i in range(1, 8)
                       if not pd.isnull(self.get_value(
                           day_df, f'comment {i}'))])[:COMMENT_LENGTH]
        )

        # add block to daily if block name is valid for the project
        block_name = self.get_value(day_df, 'block')
        if block_name in [b.block_name for b in project.blocks.all()]:
            day.block = Block.objects.get(project=project, block_name=block_name)

        day.save()

        # create/ update source production values
        try:
            prod = SourceProduction.objects.create(
                daily=day,
                sourcetype=day.project.sourcetypes.get(
                    sourcetype_name=sourcetype_name[:NAME_LENGTH])
            )

        except IntegrityError:
            prod = SourceProduction.objects.get(
                daily=day,
                sourcetype=day.project.sourcetypes.get(
                    sourcetype_name=sourcetype_name[:NAME_LENGTH])
            )

        prod.sp_t1_flat = int(np.nan_to_num(self.get_value(day_df, 'sp_t1')))
        prod.sp_t2_rough = int(np.nan_to_num(self.get_value(day_df, 'sp_t2')))
        prod.sp_t3_facilities = int(np.nan_to_num(self.get_value(day_df, 'sp_t3')))
        prod.sp_t4_dunes = int(np.nan_to_num(self.get_value(day_df, 'sp_t4')))
        prod.sp_t5_sabkha = int(np.nan_to_num(self.get_value(day_df, 'sp_t5')))
        prod.skips = int(np.nan_to_num(self.get_value(day_df, 'skips')))
        prod.save()

        # create/ update receiver production value
        try:
            rcvr = ReceiverProduction.objects.create(
                daily=day,
                receivertype=day.project.receivertypes.get(
                    receivertype_name=receivertype_name[:NAME_LENGTH])
            )

        except IntegrityError:
            rcvr = ReceiverProduction.objects.get(
                daily=day,
                receivertype=day.project.receivertypes.get(
                    receivertype_name=receivertype_name[:NAME_LENGTH])
            )

        rcvr.layout = int(np.nan_to_num(self.get_value(day_df, 'layout')))
        rcvr.pickup = int(np.nan_to_num(self.get_value(day_df, 'pickup')))
        rcvr.node_download = int(np.nan_to_num(self.get_value(day_df, 'node download')))
        rcvr.node_charged = int(np.nan_to_num(self.get_value(day_df, 'node charged')))
        rcvr.node_failure = int(np.nan_to_num(self.get_value(day_df, 'node failure')))
        rcvr.node_repair = int(np.nan_to_num(self.get_value(day_df, 'node repair')))
        rcvr.save()

        # create/ update time breakdown values
        try:
            time_breakdown = TimeBreakdown.objects.create(daily=day)

        except IntegrityError:
            time_breakdown = TimeBreakdown.objects.get(daily=day)

        time_breakdown.rec_hours = np.nan_to_num(self.get_value(day_df, 'rec hours'))
        time_breakdown.rec_moveup = np.nan_to_num(self.get_value(day_df, 'rec moveup'))
        time_breakdown.logistics = np.nan_to_num(self.get_value(day_df, 'logistics'))
        time_breakdown.camp_move = np.nan_to_num(self.get_value(day_df, 'camp move'))
        time_breakdown.wait_source = np.nan_to_num(self.get_value(day_df, 'wait source'))
        time_breakdown.wait_layout = np.nan_to_num(self.get_value(day_df, 'wait layout'))
        time_breakdown.wait_shift_change = np.nan_to_num(
            self.get_value(day_df, 'wait shift change'))
        time_breakdown.company_suspension = np.nan_to_num(
            self.get_value(day_df, 'company suspension'))
        time_breakdown.company_tests = np.nan_to_num(
            self.get_value(day_df, 'company tests'))
        time_breakdown.beyond_control = np.nan_to_num(
            self.get_value(day_df, 'beyond contractor control'))
        time_breakdown.line_fault = np.nan_to_num(
            self.get_value(day_df, 'line fault')) # No longer used
        time_breakdown.rec_eqpmt_fault = np.nan_to_num(
            self.get_value(day_df, 'Rec. eqpmt fault'))
        time_breakdown.vibrator_fault = np.nan_to_num(
            self.get_value(day_df, 'vibrator fault'))
        time_breakdown.incident = np.nan_to_num(self.get_value(day_df, 'incident'))
        time_breakdown.legal_dispute = np.nan_to_num(
            self.get_value(day_df, 'Legal/ dispute'))
        time_breakdown.comp_instruction = np.nan_to_num(
            self.get_value(day_df, 'DT comp. instruction'))
        time_breakdown.contractor_noise = np.nan_to_num(
            self.get_value(day_df, 'Contractor noise'))
        time_breakdown.other_downtime = np.nan_to_num(self.get_value(day_df, 'other dt'))
        time_breakdown.save()

        # create/ update time hseweather values
        try:
            hse_weather = HseWeather.objects.create(daily=day)

        except IntegrityError:
            hse_weather = HseWeather.objects.get(daily=day)

        hse_weather.stop = int(np.nan_to_num(self.get_value(day_df, 'hse stop cards')))
        hse_weather.lti = int(np.nan_to_num(self.get_value(day_df, 'hse lti')))
        hse_weather.fac = int(np.nan_to_num(self.get_value(day_df, 'hse fac')))
        hse_weather.mtc = int(np.nan_to_num(self.get_value(day_df, 'hse mtc')))
        hse_weather.rwc = int(np.nan_to_num(self.get_value(day_df, 'hse RWC')))
        hse_weather.incident_nm = int(
            np.nan_to_num(self.get_value(day_df, 'hse incident or nm')))
        hse_weather.medevac = int(np.nan_to_num(self.get_value(day_df, 'hse medevac')))
        hse_weather.drills = int(np.nan_to_num(self.get_value(day_df, 'hse drills')))
        hse_weather.audits = int(np.nan_to_num(self.get_value(day_df, 'hse audits')))
        hse_weather.lsr_violations = int(
            np.nan_to_num(self.get_value(day_df, 'hse lsr violation')))
        hse_weather.headcount = np.nan_to_num(self.get_value(day_df, 'headcount'))
        hse_weather.exposure_hours = np.nan_to_num(self.get_value(
            day_df, 'exposure hours'))
        hse_weather.weather_condition = str(self.get_value(
            day_df, 'weather condition'))[:NAME_LENGTH]
        hse_weather.rain = str(self.get_value(day_df, 'rain'))[:NAME_LENGTH]
        hse_weather.temp_min = np.nan_to_num(self.get_value(day_df, 'temp min'))
        hse_weather.temp_max = np.nan_to_num(self.get_value(day_df, 'temp max'))
        hse_weather.save()

        # delete toolboxes and then (re)create
        toolboxes = ToolBox.objects.filter(hse=hse_weather)
        for toolbox in toolboxes:
            toolbox.delete()

        for i in range(1, 9):
            toolbox_topic = self.get_value(day_df, f'toolbox {i}')
            try:
                if np.isnan(toolbox_topic):
                    continue

            except TypeError:
                pass

            if toolbox_topic:
                ToolBox.objects.create(
                    hse=hse_weather, toolbox=toolbox_topic.rstrip('\n')[:DESCR_LENGTH])

        return day.production_date

    @staticmethod
    def calc_day_prod_totals(daily, sourcetype_name):
        if daily:
            try:
                prod = SourceProduction.objects.get(
                    daily=daily,
                    sourcetype=daily.project.sourcetypes.get(
                        sourcetype_name=sourcetype_name)
                )

            except SourceProduction.DoesNotExist:
                dp = {f'{key[:5]}': np.nan for key in source_prod_schema}
                dp['total_sp'] = np.nan
                dp['tcf'] = np.nan
                return dp

        else:
            dp = {f'{key[:5]}': np.nan for key in source_prod_schema}
            dp['total_sp'] = np.nan
            dp['tcf'] = np.nan
            dp['vp_hour'] = np.nan
            return dp

        dp = {f'{key[:5]}': np.nan_to_num(getattr(prod, key))
              for key in source_prod_schema}

        # exclude last key for skips
        dp['total_sp'] = np.nansum(
            [dp[f'{key[:5]}'] for key in source_prod_schema[:-1]]
        )

        if dp['total_sp'] > 0:
            dp['tcf'] = sum(dp[key[:5]] / dp['total_sp'] * TCF_table[key[6:]]
                            for key in source_prod_schema[:-1])

        else:
            dp['tcf'] = np.nan

        return dp

    @staticmethod
    def calc_week_prod_totals(daily, sourcetype_name):
        if daily:
            end_date = daily.production_date
            start_date = end_date - timedelta(days=WEEKDAYS-1)

            sp_query = SourceProduction.objects.filter(
                Q(daily__production_date__gte=start_date),
                Q(daily__production_date__lte=end_date),
                sourcetype=daily.project.sourcetypes.get(sourcetype_name=sourcetype_name),
            )

        else:
            sp_query = None

        if not sp_query:
            wp = {f'week_{key[:5]}': np.nan for key in source_prod_schema}
            wp['week_total'] = np.nan
            wp['week_tcf'] = np.nan
            wp['week_vp_hour'] = np.nan
            wp['week_avg'] = np.nan
            wp['week_perc_skips'] = np.nan
            return wp

        wp = {f'week_{key[:5]}': np.nansum([val[key] for val in sp_query.values()])
              for key in source_prod_schema}

        # exclude last key for skips
        wp['week_total'] = np.sum(
            wp[f'week_{key[:5]}'] for key in source_prod_schema[:-1]
        )

        if wp['week_total'] > 0:
            wp['week_tcf'] = sum(
                wp[f'week_{key[:5]}'] / wp['week_total'] * TCF_table[key[6:]]
                for key in source_prod_schema[:-1]
            )
            wp['week_avg'] = round(wp['week_total'] / len(sp_query))
            wp['week_perc_skips'] = (
                wp['week_skips'] / (wp['week_total'] + wp['week_skips'])
            )

        else:
            wp['week_tcf'] = np.nan
            wp['week_avg'] = np.nan
            wp['week_perc_skips'] = np.nan

        return wp

    @staticmethod
    def calc_month_prod_totals(daily, sourcetype_name):
        # filter for days in the month up to and including the production date
        sp_query = SourceProduction.objects.filter(
            Q(daily__production_date__year=daily.production_date.year) &
            Q(daily__production_date__month=daily.production_date.month) &
            Q(daily__production_date__day__lte=daily.production_date.day),
            sourcetype=daily.project.sourcetypes.get(sourcetype_name=sourcetype_name),
        )

        if not sp_query:
            mp = {f'month_{key[:5]}': np.nan for key in source_prod_schema}
            mp['month_total'] = np.nan
            mp['month_tcf'] = np.nan
            mp['month_vp_hour'] = np.nan
            mp['month_avg'] = np.nan
            mp['month_perc_skips'] = np.nan
            return mp


        mp = {f'month_{key[:5]}': np.nansum([val[key] for val in sp_query.values()])
              for key in source_prod_schema}

        # exclude last key for skips
        mp['month_total'] = np.sum(
            mp[f'month_{key[:5]}'] for key in source_prod_schema[:-1]
        )

        if mp['month_total'] > 0:
            mp['month_tcf'] = sum(
                mp[f'month_{key[:5]}'] / mp['month_total'] * TCF_table[key[6:]]
                for key in source_prod_schema[:-1]
            )
            mp['month_avg'] = round(mp['month_total'] / len(sp_query))
            mp['month_perc_skips'] = (
                mp['month_skips'] / (mp['month_total'] + mp['month_skips'])
            )
        else:
            mp['month_tcf'] = np.nan
            mp['month_avg'] = np.nan
            mp['month_perc_skips'] = np.nan

        return mp

    def calc_proj_prod_totals(self, daily, sourcetype_name):
        # filter for all days in the project up to and including the production date
        sp_query = SourceProduction.objects.filter(
            daily__production_date__lte=daily.production_date,
            sourcetype=daily.project.sourcetypes.get(sourcetype_name=sourcetype_name),
        ).order_by('daily__production_date')

        if not sp_query:
            pp = {f'proj_{key[:5]}': np.nan for key in source_prod_schema}
            pp['proj_total'] = np.nan
            pp['proj_tcf'] = np.nan
            pp['proj_vp_hour'] = np.nan
            pp['proj_avg'] = np.nan
            pp['proj_perc_skips'] = np.nan
            return pp, {}

        p_series = {f'{key[:5]}_series': nan_array(
            [val[key] for val in sp_query.values()]) for key in source_prod_schema}
        p_series['terrain_series'] = list(zip(
            *[val for key, val in p_series.items() if key != 'skips_series']
        ))
        p_series['date_series'] = np.array(
            [val.daily.production_date for val in sp_query])
        p_series['tcf_series'] = []
        p_series['total_sp_series'] = []
        for terrain_sp in p_series['terrain_series']:
            sp_total = np.nansum(terrain_sp)
            p_series['total_sp_series'].append(sp_total)
            if sp_total > 0:
                p_series['tcf_series'].append(
                    terrain_sp[0] / sp_total * TCF_table['flat'] +
                    terrain_sp[1] / sp_total * TCF_table['rough'] +
                    terrain_sp[2] / sp_total * TCF_table['facilities'] +
                    terrain_sp[3] / sp_total * TCF_table['dunes'] +
                    terrain_sp[4] / sp_total * TCF_table['sabkha']
                )

            else:
                p_series['tcf_series'].append(np.nan)



        pp = {f'proj_{key[:5]}': np.nansum(
            p_series[f'{key[:5]}_series']) for key in source_prod_schema}

        # exclude last key 'skips' from total
        pp['proj_total'] = np.sum(
            pp[f'proj_{key[:5]}'] for key in source_prod_schema[:-1]
        )

        if pp['proj_total'] > 0:
            pp['proj_tcf'] = sum(
                pp[f'proj_{key[:5]}'] / pp['proj_total'] * TCF_table[key[6:]]
                for key in source_prod_schema[:-1]
            )
            if (daily.project.planned_start_date and pp['proj_total'] and
                (p_days := (daily.production_date - daily.project.planned_start_date).days + 1) > 0):  #pylint: disable=line-too-long
                pp['proj_avg'] = round(pp['proj_total'] / p_days)

            else:
                pp['proj_avg'] = np.nan

            pp['proj_perc_skips'] = (
                pp['proj_skips'] / (pp['proj_total'] + pp['proj_skips'])
            )

        else:
            pp['proj_tcf'] = np.nan
            pp['proj_avg'] = np.nan
            pp['proj_perc_skips']= np.nan

        return pp, p_series

    @staticmethod
    def calc_day_time_totals(daily):
        try:
            tb = TimeBreakdown.objects.get(daily=daily)

        except TimeBreakdown.DoesNotExist:
            dt = {f'{key}': np.nan for key in time_breakdown_schema}
            dt['rec_time'] = np.nan
            dt['ops_time'] = np.nan
            dt['standby'] = np.nan
            dt['downtime'] = np.nan
            dt['total_time'] = np.nan
            return dt

        dt = {f'{key}': np.nan_to_num(getattr(tb, key)) for key in time_breakdown_schema}

        dt['rec_time'] = np.nansum(tb.rec_hours)
        dt['ops_time'] = np.nansum([getattr(tb, key) for key in ops_time_keys])
        dt['standby'] = np.nansum([getattr(tb, key) for key in standby_keys])
        dt['downtime'] = np.nansum([getattr(tb, key) for key in downtime_keys])
        dt['total_time'] = np.nansum([
            dt['ops_time'], dt['standby'], dt['downtime'],
        ])

        return dt

    @staticmethod
    def calc_week_time_totals(daily):
        if daily:
            end_date = daily.production_date
            start_date = end_date - timedelta(days=WEEKDAYS-1)

            tb_query = TimeBreakdown.objects.filter(
                Q(daily__production_date__gte=start_date),
                Q(daily__production_date__lte=end_date),
                daily__project=daily.project,
            )

        else:
            tb_query = None

        if not tb_query:
            wt = {f'week_{key}': np.nan for key in time_breakdown_schema}
            wt['week_rec_time'] = np.nan
            wt['week_ops_time'] = np.nan
            wt['week_standby'] = np.nan
            wt['week_downtime'] = np.nan
            wt['week_total_time'] = np.nan
            return wt

        wt = {f'week_{key}': np.nansum([val[key] for val in tb_query.values()])
              for key in time_breakdown_schema}

        wt['week_rec_time'] = wt['week_rec_hours']
        wt['week_ops_time'] = np.nansum([wt[f'week_{key}'] for key in ops_time_keys])
        wt['week_standby'] = np.nansum([wt[f'week_{key}'] for key in standby_keys])
        wt['week_downtime'] = np.nansum([wt[f'week_{key}'] for key in downtime_keys])
        wt['week_total_time'] = np.nansum([
            wt['week_ops_time'], wt['week_standby'], wt['week_downtime']
        ])

        return wt

    @staticmethod
    def calc_month_time_totals(daily):
        tb_query = TimeBreakdown.objects.filter(
            Q(daily__production_date__year=daily.production_date.year) &
            Q(daily__production_date__month=daily.production_date.month) &
            Q(daily__production_date__day__lte=daily.production_date.day),
            daily__project=daily.project,
        )

        if not tb_query:
            mt = {f'month_{key}': np.nan for key in time_breakdown_schema}
            mt['month_rec_time'] = np.nan
            mt['month_ops_time'] = np.nan
            mt['month_standby'] = np.nan
            mt['month_downtime'] = np.nan
            mt['month_total_time'] = np.nan
            return mt


        mt = {f'month_{key}': np.nansum([val[key] for val in tb_query.values()])
              for key in time_breakdown_schema}

        mt['month_rec_time'] = mt['month_rec_hours']
        mt['month_ops_time'] = np.nansum([mt[f'month_{key}'] for key in ops_time_keys])
        mt['month_standby'] = np.nansum([mt[f'month_{key}'] for key in standby_keys])
        mt['month_downtime'] = np.nansum([mt[f'month_{key}'] for key in downtime_keys])
        mt['month_total_time'] = np.nansum([
            mt['month_ops_time'], mt['month_standby'], mt['month_downtime']
        ])

        return mt

    def calc_proj_time_totals(self, daily):
        tb_query = TimeBreakdown.objects.filter(
            daily__production_date__lte=daily.production_date,
            daily__project=daily.project,
        ).order_by('daily__production_date')

        if not tb_query:
            pt = {f'proj_{key}': np.nan for key in time_breakdown_schema}
            pt['proj_rec_time'] = np.nan
            pt['proj_ops_time'] = np.nan
            pt['proj_standby'] = np.nan
            pt['proj_downtime'] = np.nan
            pt['proj_total_time'] = np.nan
            return pt, {}


        ts = {f'{key}_series': nan_array([val[key] for val in tb_query.values()])
              for key in time_breakdown_schema}

        ts['ops_series'] = sum(ts[f'{key}_series'] for key in ops_time_keys)
        ts['standby_series'] = sum(ts[f'{key}_series'] for key in standby_keys)
        ts['downtime_series'] = sum(ts[f'{key}_series'] for key in downtime_keys)
        ts['total_time_series'] = (
            ts['ops_series'] + ts['standby_series'] + ts['downtime_series']
        )
        ts['date_series'] = np.array([val.daily.production_date for val in tb_query])

        pt = {f'proj_{key}': np.nansum(ts[f'{key}_series'])
              for key in time_breakdown_schema}
        pt['proj_rec_time'] = pt['proj_rec_hours']
        pt['proj_ops_time'] = np.nansum([pt[f'proj_{key}'] for key in ops_time_keys])
        pt['proj_standby'] = np.nansum([pt[f'proj_{key}'] for key in standby_keys])
        pt['proj_downtime'] = np.nansum([pt[f'proj_{key}'] for key in downtime_keys])
        pt['proj_total_time'] = np.nansum([
            pt['proj_ops_time'], pt['proj_standby'], pt['proj_downtime'],
        ])

        return pt, ts

    def calc_totals(self, daily):
        if not daily:
            return {}, {}, {}

        # get time breakdown stats
        day_times = self.calc_day_time_totals(daily)
        week_times = self.calc_week_time_totals(daily)
        month_times = self.calc_month_time_totals(daily)
        proj_times, self.time_series = self.calc_proj_time_totals(daily)

        # TODO make loop over source types
        sourcetype_name, _ = get_sourcereceivertype_names(daily)

        # get the production stats
        day_prod = self.calc_day_prod_totals(daily, sourcetype_name)
        day_ctm = self.calc_ctm(daily, sourcetype_name, day_prod['tcf'])

        week_prod = self.calc_week_prod_totals(daily, sourcetype_name)
        week_ctm = self.calc_ctm(daily, sourcetype_name, week_prod['week_tcf'])

        month_prod = self.calc_month_prod_totals(daily, sourcetype_name)
        month_ctm = self.calc_ctm(daily, sourcetype_name, month_prod['month_tcf'])

        proj_prod, self.prod_series = self.calc_proj_prod_totals(daily, sourcetype_name)
        proj_ctm = self.calc_ctm(daily, sourcetype_name, proj_prod['proj_tcf'])

        if CTM_METHOD == 'Legacy':
            day_ctm *= day_times['total_time'] / 24

        else:
            day_ctm *= (day_times['total_time'] - day_times['standby']) / 24

        day_app_ctm = calc_ratio(day_prod['total_sp'], day_ctm)
        day_rate = self.calc_rate(
            daily, CTM_METHOD, day_app_ctm, day_times['total_time'], day_times['standby']
        )
        day_ctm = round(day_ctm) if not np.isnan(day_ctm) else 0
        day_prod['ctm'] = (day_ctm, day_app_ctm, day_rate)
        day_prod['vp_hour'] = (
            round(day_prod['total_sp'] / day_times['rec_time'])
            if day_times['rec_time'] else np.nan
        )

        if CTM_METHOD == 'Legacy':
            week_ctm *= week_times['week_total_time'] / 24

        else:
            week_ctm *= (week_times['week_total_time'] - week_times['week_standby']) / 24

        week_app_ctm = calc_ratio(week_prod['week_total'], week_ctm)
        week_rate = self.calc_rate(
            daily, CTM_METHOD, week_app_ctm,
            week_times['week_total_time'], week_times['week_standby']
        )
        week_ctm = round(week_ctm) if not np.isnan(week_ctm) else 0
        week_prod['week_ctm'] = (week_ctm, week_app_ctm, week_rate)
        week_prod['week_vp_hour'] = (
            round(week_prod['week_total'] / week_times['week_rec_time'])
            if week_times['week_rec_time'] else np.nan
        )

        if CTM_METHOD == 'Legacy':
            month_ctm *= month_times['month_total_time'] / 24

        else:
            month_ctm *= (
                (month_times['month_total_time'] - month_times['month_standby']) / 24
            )

        month_app_ctm = calc_ratio(month_prod['month_total'], month_ctm)
        month_rate = self.calc_rate(
            daily, CTM_METHOD, month_app_ctm,
            month_times['month_total_time'], month_times['month_standby']
        )
        month_ctm = round(month_ctm) if not np.isnan(month_ctm) else 0
        month_prod['month_ctm'] = (month_ctm, month_app_ctm, month_rate)
        month_prod['month_vp_hour'] = (
            round(month_prod['month_total'] / month_times['month_rec_time'])
            if month_times['month_rec_time'] else np.nan
        )

        if CTM_METHOD == 'Legacy':
            proj_ctm *= proj_times['proj_total_time'] / 24

        else:
            proj_ctm *= (proj_times['proj_total_time'] - proj_times['proj_standby']) / 24

        proj_app_ctm = calc_ratio(proj_prod['proj_total'], proj_ctm)
        proj_rate = self.calc_rate(
            daily, CTM_METHOD, proj_app_ctm,
            proj_times['proj_total_time'], proj_times['proj_standby']
        )
        proj_ctm = round(proj_ctm) if not np.isnan(proj_ctm) else 0
        proj_prod['proj_ctm'] = (proj_ctm, proj_app_ctm, proj_rate)
        proj_prod['proj_vp_hour'] = (
            round(proj_prod['proj_total'] / proj_times['proj_rec_time'])
            if proj_times['proj_rec_time'] else np.nan
        )

        ctm_series = self.calc_ctm_series(
            daily, sourcetype_name, self.prod_series['tcf_series'])

        if CTM_METHOD == 'Legacy':
            ops_time_series = self.time_series['total_time_series']

        else:
            ops_time_series = (
                self.time_series['total_time_series'] - self.time_series['standby_series']
            )
        ctm_series = ctm_series * ops_time_series / 24
        total_sp_series = np.array(
            [sum(terrain) for terrain in self.prod_series['terrain_series']])
        app_ctm_series = np.array(
            [calc_ratio(total_sp, ctm)
             for total_sp, ctm in zip(total_sp_series, ctm_series)])
        self.prod_series['ctm_series'] = np.array(list(zip(ctm_series, app_ctm_series)))

        # get the HSE stats
        day_hse = self.day_hse_totals(daily)
        week_hse = self.week_hse_totals(daily)
        month_hse = self.month_hse_totals(daily)
        proj_hse, self.hse_series = self.proj_hse_totals(daily)

        prod_total = {**day_prod, **week_prod, **month_prod, **proj_prod}
        times_total = {**day_times, **week_times, **month_times, **proj_times}
        hse_total = {**day_hse, **week_hse, **month_hse, **proj_hse}

        return prod_total, times_total, hse_total

    @property
    def series(self) -> typing.Optional[tuple]:
        return self.prod_series, self.time_series, self.hse_series

    def calc_block_totals(self, daily):
        ''' A naive method to calculate block production totals
            Block totals are calculated for the block reported for the day
            All Vps for a day that have the same block name will be included
            even Vps are acquired on different blocks
            Also it takes Vps for all sourcetypes
        '''
        if not daily:
            return {}

        sp_query = SourceProduction.objects.filter(
            daily__production_date__lte=daily.production_date,
            daily__project=daily.project,
            daily__block=daily.block,
        ).order_by('daily__production_date')

        if not sp_query:
            return {}

        bp = {f'block_{key[:5]}': np.nansum([val[key] for val in sp_query.values()])
              for key in source_prod_schema}

        # exclude last key for skips to calculate the total
        bp['block_total'] = np.sum(
            bp[f'block_{key[:5]}'] for key in source_prod_schema[:-1]
        )

        return bp

    def calc_est_completion_date(
        self, daily, period: int, planned: int, complete: float):
        ''' Method to calculate the estimated completion date based on:
            current date, avg production over period before current date,
            planned points and percemtage complete to date.
            returns: str with date in format "DD MM YYYY" or NO_DATE_STR
        '''
        if not daily or period < 1:
            return NO_DATE_STR

        # check if we have passed the last production date, based on zero production today
        # and completion greater than (arbitrary) 0.97, in that case find the last
        # production date
        if complete > 0.97:
            if SourceProduction.objects.filter(
                Q(sp_t1_flat=0) &
                Q(sp_t2_rough=0) &
                Q(sp_t3_facilities=0) &
                Q(sp_t4_dunes=0) &
                Q(sp_t5_sabkha=0),
                daily=daily):
                return self.get_last_production_date(daily.project)

        # calculate total sp including skips and avg_prod
        end_date = daily.production_date
        start_date = end_date - timedelta(days=period)
        sp_query = SourceProduction.objects.filter(
            daily__production_date__range=(start_date, end_date),
            daily__project=daily.project,
        )

        if not sp_query:
            return NO_DATE_STR

        sps_dict = {f'{key[:5]}': np.nansum([val[key] for val in sp_query.values()])
                    for key in source_prod_schema}
        total_sp = np.sum(sps_dict[f'{key[:5]}'] for key in source_prod_schema)
        avg_prod = total_sp / period

        remaining = (1 - complete) * planned
        if avg_prod > 0:
            est_completion = (daily.production_date + timedelta(
                    days=remaining / avg_prod)).strftime('%#d %b %Y')

        else:
            est_completion = NO_DATE_STR


        return est_completion

    def get_last_production_date(self, project) -> str:
        ''' Method to get the last date where was production for project
            Returns: date in format "DD MMM YYYY" or NO_DATE_STR
        '''
        if not project:
            return NO_DATE_STR

        last_production = SourceProduction.objects.filter(
            Q(sp_t1_flat__gt=0) |
            Q(sp_t2_rough__gt=0) |
            Q(sp_t3_facilities__gt=0) |
            Q(sp_t4_dunes__gt=0) |
            Q(sp_t5_sabkha__gt=0),
            daily__project=project).order_by('daily__production_date').last()

        if last_production:
            return last_production.daily.production_date.strftime('%#d %b %Y')

        else:
            return NO_DATE_STR
