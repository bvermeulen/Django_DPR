from datetime import datetime, timedelta
import os
import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import matplotlib.dates as mdates
from django.db.utils import IntegrityError
from django.db.models import Q
from daily_report.models.daily_models import (
    Daily, SourceProduction, TimeBreakdown, HseWeather, ToolBox,
)
from daily_report.models.project_models import Project, Block
from daily_report.hseweather_backend import HseInterface
from seismicreport.vars import (
    TCF_table, BGP_DR_table, SOURCETYPE_NAME, source_prod_schema, time_breakdown_schema,
    ops_time_keys, standby_keys, downtime_keys, NAME_LENGTH, DESCR_LENGTH, COMMENT_LENGTH,
    NO_DATE_STR,
)
from seismicreport.utils.plogger import timed, Logger
from seismicreport.utils.utils_funcs import calc_ratio, nan_array


#pylint: disable=no-value-for-parameter
matplotlib.use('Agg')

TICK_SPACING_PROD = 5  # x 1000
TICK_SPACING_CUMUL = 1000  # x 1000
TICK_DATE_FORMAT = mdates.DateFormatter('%d-%b-%y')

logger = Logger.getlogger()

class ReportInterface(HseInterface):

    def __init__(self, media_dir):
        self.media_dir = media_dir
        self.prod_series = None
        self.time_series = None

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

    @staticmethod
    def calc_ctm(daily, sourcetype_name, tcf):
        if not daily or np.isnan(tcf):
            return np.nan

        sourcetype_obj = daily.project.sourcetypes.get(sourcetype_name=sourcetype_name)
        mpr_vibes = sourcetype_obj.mpr_vibes
        mpr_sweep = sourcetype_obj.mpr_sweep_length
        mpr_moveup = sourcetype_obj.mpr_moveup
        mpr_rec_hours = sourcetype_obj.mpr_rec_hours

        if mpr_vibes == 0 or mpr_sweep == 0 or mpr_moveup == 0:
            return np.nan

        ctm = int(3600 / (mpr_sweep + mpr_moveup) * mpr_vibes * tcf * mpr_rec_hours)

        return ctm

    def calc_ctm_series(self, daily, sourcetype_name, tcf_series):
        ctm_series = []
        for tcf in tcf_series:
            ctm_series.append(self.calc_ctm(daily, sourcetype_name, tcf))

        return np.array(ctm_series)

    @staticmethod
    def calc_rate(daily, app_ctm, total_time, standby_time):
        ''' IMH opinion correct calculation of the rate
        '''
        standby_rate = daily.project.standby_rate
        cap_rate = daily.project.cap_rate
        cap_app_ctm = daily.project.cap_app_ctm
        if app_ctm > 1 and cap_app_ctm > 1 and cap_rate > 1:
            app_ctm = 1 + (cap_rate - 1) * min((app_ctm - 1) / (cap_app_ctm - 1), 1)

        return ((app_ctm * (total_time - standby_time) + standby_rate * standby_time) /
                total_time)

    @staticmethod
    def calc_rate_current(daily, app_ctm, total_time, standby_time):
        ''' IMH opinion correct calculation of the rate
        '''
        standby_rate = daily.project.standby_rate
        cap_rate = daily.project.cap_rate
        cap_app_ctm = daily.project.cap_app_ctm
        app_ctm *= (total_time - standby_time) / total_time
        if app_ctm > 1 and cap_app_ctm > 1 and cap_rate > 1:
            app_ctm = 1 + (cap_rate - 1) * min((app_ctm - 1) / (cap_app_ctm - 1), 1)

        return (app_ctm * total_time + standby_rate * standby_time) / total_time

    def save_report_file(self, project, report_file) -> datetime:
        report_date = self.populate_report(project, report_file.temporary_file_path())
        report_file.close()

        return report_date

    @staticmethod
    @timed(logger, print_log=True)
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

    @timed(logger, print_log=True)
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

        day.pm_comment = (
            '\n'.join([str(self.get_value(day_df, f'comment {i}')) for i in range(1, 7)
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
                    sourcetype_name=SOURCETYPE_NAME[:NAME_LENGTH])
            )

        except IntegrityError:
            prod = SourceProduction.objects.get(
                daily=day,
                sourcetype=day.project.sourcetypes.get(
                    sourcetype_name=SOURCETYPE_NAME[:NAME_LENGTH])
            )

        prod.sp_t1_flat = int(np.nan_to_num(self.get_value(day_df, 'sp_t1')))
        prod.sp_t2_rough = int(np.nan_to_num(self.get_value(day_df, 'sp_t2')))
        prod.sp_t3_facilities = int(np.nan_to_num(self.get_value(day_df, 'sp_t3')))
        prod.sp_t4_dunes = int(np.nan_to_num(self.get_value(day_df, 'sp_t4')))
        prod.sp_t5_sabkha = int(np.nan_to_num(self.get_value(day_df, 'sp_t5')))
        prod.skips = int(np.nan_to_num(self.get_value(day_df, 'skips')))
        prod.save()

        # create/ update time breakdown values
        try:
            time_breakdown = TimeBreakdown.objects.create(daily=day)

        except IntegrityError:
            time_breakdown = TimeBreakdown.objects.get(daily=day)

        time_breakdown.rec_hours = self.get_value(day_df, 'rec hours')
        time_breakdown.rec_moveup = self.get_value(day_df, 'rec moveup')
        time_breakdown.logistics = self.get_value(day_df, 'logistics')
        time_breakdown.camp_move = self.get_value(day_df, 'camp move')
        time_breakdown.wait_source = self.get_value(day_df, 'wait source')
        time_breakdown.wait_layout = self.get_value(day_df, 'wait layout')
        time_breakdown.wait_shift_change = self.get_value(day_df, 'wait shift change')
        time_breakdown.company_suspension = self.get_value(day_df, 'company suspension')
        time_breakdown.company_tests = self.get_value(day_df, 'company tests')
        time_breakdown.beyond_control = self.get_value(day_df, 'beyond contractor control')  #pylint: disable=line-too-long
        time_breakdown.line_fault = self.get_value(day_df, 'line fault')
        time_breakdown.instrument_fault = self.get_value(day_df, 'instrument fault')
        time_breakdown.vibrator_fault = self.get_value(day_df, 'vibrator fault')
        time_breakdown.incident = self.get_value(day_df, 'incident')
        time_breakdown.holiday = self.get_value(day_df, 'holiday')
        time_breakdown.recovering = self.get_value(day_df, 'recovering')
        time_breakdown.other_downtime = self.get_value(day_df, 'other dt')
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
        hse_weather.ops_time = np.nan_to_num(self.get_value(day_df, 'ops time'))
        hse_weather.day_time = np.nan_to_num(self.get_value(day_df, 'day time'))
        hse_weather.weather_condition = self.get_value(
            day_df, 'weather condition')[:NAME_LENGTH]
        hse_weather.rain = self.get_value(day_df, 'rain')[:NAME_LENGTH]
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
    @timed(logger, print_log=True)
    def calc_day_prod_totals(daily, sourcetype_name):
        try:
            prod = SourceProduction.objects.get(
                daily=daily,
                sourcetype=daily.project.sourcetypes.get(sourcetype_name=sourcetype_name)
            )

        except SourceProduction.DoesNotExist:
            return {}

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
    @timed(logger, print_log=True)
    def calc_month_prod_totals(daily, sourcetype_name):
        # filter for days in the month up to and including the production date
        sp_query = SourceProduction.objects.filter(
            Q(daily__production_date__year=daily.production_date.year) &
            Q(daily__production_date__month=daily.production_date.month) &
            Q(daily__production_date__day__lte=daily.production_date.day),
            sourcetype=daily.project.sourcetypes.get(sourcetype_name=sourcetype_name),
            daily__project=daily.project,
        )

        if not sp_query:
            return {}

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

        else:
            mp['month_tcf'] = np.nan

        return mp

    @timed(logger, print_log=True)
    def calc_proj_prod_totals(self, daily, sourcetype_name):
        # filter for all days in the project up to and including the production date
        sp_query = SourceProduction.objects.filter(
            daily__production_date__lte=daily.production_date,
            sourcetype=daily.project.sourcetypes.get(sourcetype_name=sourcetype_name),
            daily__project=daily.project,
        ).order_by('daily__production_date')

        if not sp_query:
            return {}

        p_series = {f'{key[:5]}_series': nan_array(
            [val[key] for val in sp_query.values()]) for key in source_prod_schema}
        p_series['terrain_series'] = list(zip(
            *[val for key, val in p_series.items() if key != 'skips_series']
        ))
        p_series['date_series'] = np.array(
            [val.daily.production_date for val in sp_query])
        p_series['tcf_series'] = []
        for terrain_sp in p_series['terrain_series']:
            sp_total = np.nansum(terrain_sp)
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

        else:
            pp['proj_total'] = np.nan
            pp['proj_tcf'] = np.nan

        return pp, p_series

    @staticmethod
    @timed(logger, print_log=True)
    def calc_day_time_totals(daily):
        try:
            tb = TimeBreakdown.objects.get(daily=daily)

        except TimeBreakdown.DoesNotExist:
            return {}

        dt = {f'{key}': np.nan_to_num(getattr(tb, key)) for key in time_breakdown_schema}

        dt['rec_time'] = np.nansum(tb.rec_hours)
        dt['ops_time'] = np.nansum([getattr(tb, key) for key in ops_time_keys])
        dt['standby'] = np.nansum([getattr(tb, key) for key in standby_keys])
        dt['downtime'] = np.nansum([getattr(tb, key) for key in downtime_keys])
        dt['total_time'] = np.nansum([
            dt['rec_time'], dt['ops_time'], dt['standby'], dt['downtime'],
        ])

        return dt

    @staticmethod
    @timed(logger, print_log=True)
    def calc_month_time_totals(daily):
        tb_query = TimeBreakdown.objects.filter(
            Q(daily__production_date__year=daily.production_date.year) &
            Q(daily__production_date__month=daily.production_date.month) &
            Q(daily__production_date__day__lte=daily.production_date.day),
            daily__project=daily.project,
        )

        if not tb_query:
            return {}

        mt = {f'month_{key}': np.nansum([val[key] for val in tb_query.values()])
              for key in time_breakdown_schema}

        mt['month_rec_time'] = mt['month_rec_hours']
        mt['month_ops_time'] = np.nansum([mt[f'month_{key}'] for key in ops_time_keys])
        mt['month_standby'] = np.nansum([mt[f'month_{key}'] for key in standby_keys])
        mt['month_downtime'] = np.nansum([mt[f'month_{key}'] for key in downtime_keys])
        mt['month_total_time'] = np.nansum([
            mt['month_rec_time'], mt['month_ops_time'], mt['month_standby'],
            mt['month_downtime']
        ])

        return mt

    @timed(logger, print_log=True)
    def calc_proj_time_totals(self, daily):
        tb_query = TimeBreakdown.objects.filter(
            daily__production_date__lte=daily.production_date,
            daily__project=daily.project,
        ).order_by('daily__production_date')

        if not tb_query:
            return {}

        ts = {f'{key}_series': nan_array([val[key] for val in tb_query.values()])
              for key in time_breakdown_schema}

        ts['ops_series'] = sum(ts[f'{key}_series'] for key in ops_time_keys)
        ts['standby_series'] = sum(ts[f'{key}_series'] for key in standby_keys)
        ts['downtime_series'] = sum(ts[f'{key}_series'] for key in downtime_keys)
        ts['total_time_series'] = (
            ts['rec_hours_series'] + ts['ops_series'] + ts['standby_series'] +
            ts['downtime_series']
        )
        ts['date_series'] = np.array([val.daily.production_date for val in tb_query])

        pt = {f'proj_{key}': np.nansum(ts[f'{key}_series'])
              for key in time_breakdown_schema}
        pt['proj_rec_time'] = pt['proj_rec_hours']
        pt['proj_ops_time'] = np.nansum([pt[f'proj_{key}'] for key in ops_time_keys])
        pt['proj_standby'] = np.nansum([pt[f'proj_{key}'] for key in standby_keys])
        pt['proj_downtime'] = np.nansum([pt[f'proj_{key}'] for key in downtime_keys])
        pt['proj_total_time'] = np.nansum([
            pt['proj_rec_time'], pt['proj_ops_time'], pt['proj_standby'],
            pt['proj_downtime'],
        ])

        return pt, ts

    @timed(logger, print_log=True)
    def create_graphs(self):
        ''' Method to make plots. This method works correctly once self.prod_series and
            self.time_series have been calculated in method calc_totals. Reason to split
            it out of that function is that this method is time consuming and better to
            avoice to run it when it is not necessary.
        '''
        if self.prod_series and self.time_series:
            date_series = self.prod_series['date_series']
            terrain_series = self.prod_series['terrain_series']
            assert len(date_series) == len(terrain_series), \
                'length date en terrain series must be equal'

        else:
            return

        # stacked bar plot of daily production
        t1_series = np.array([val[0] for val in terrain_series]) * 0.001
        t2_series = np.array([val[1] for val in terrain_series]) * 0.001
        t3_series = np.array([val[2] for val in terrain_series]) * 0.001
        t4_series = np.array([val[3] for val in terrain_series]) * 0.001
        t5_series = np.array([val[4] for val in terrain_series]) * 0.001
        base = np.zeros(len(date_series))

        width = 1
        plot_filename = os.path.join(self.media_dir, 'images', 'daily_prod.png')

        if any(t1_series):
            plt.bar(date_series, t1_series, width, label="Flat")
            base += t1_series

        if any(t2_series):
            plt.bar(date_series, t2_series, width, bottom=base, label="Rough")
            base += t2_series

        if any(t3_series):
            plt.bar(date_series, t3_series, width, bottom=base, label="Facilities")
            base += t3_series

        if any(t4_series):
            plt.bar(date_series, t4_series, width, bottom=base, label="Dunes")
            base += t4_series

        if any(t5_series):
            plt.bar(date_series, t5_series, width, bottom=base, label="Sabkha")

        total_sp_series = (base + t5_series) * 1000

        plt.gca().xaxis.set_major_formatter(TICK_DATE_FORMAT)
        plt.xticks(rotation=70)
        plt.legend()
        plt.gca().yaxis.set_major_formatter(mtick.StrMethodFormatter('{x:,.0f}k'))
        plt.gca().yaxis.set_major_locator(mtick.MultipleLocator(TICK_SPACING_PROD))
        plt.gca().yaxis.grid()
        plt.tight_layout()
        plt.savefig(plot_filename, format='png')
        plt.close()

        # line plot of cumulative production
        t1_cum = np.cumsum(t1_series)
        t2_cum = np.cumsum(t2_series)
        t3_cum = np.cumsum(t3_series)
        t4_cum = np.cumsum(t4_series)
        t5_cum = np.cumsum(t5_series)
        base = np.zeros(len(date_series))

        plot_filename = os.path.join(self.media_dir, 'images', 'cumul_prod.png')

        if any(t1_cum):
            base += t1_cum
            plt.plot(date_series, base, label="Flat")

        if any(t2_cum):
            base += t2_cum
            plt.plot(date_series, base, label="Rough")

        if any(t3_cum):
            base += t3_cum
            plt.plot(date_series, base, label="Facilities")

        if any(t4_cum):
            base += t4_cum
            plt.plot(date_series, base, label="Dunes")

        if any(t5_cum):
            base += t5_cum
            plt.plot(date_series, base, label="Sabkha")

        plt.gca().xaxis.set_major_formatter(TICK_DATE_FORMAT)
        plt.xticks(rotation=70)
        plt.legend()
        plt.gca().yaxis.set_major_formatter(mtick.StrMethodFormatter('{x:,.0f}k'))
        plt.gca().yaxis.set_major_locator(mtick.MultipleLocator(TICK_SPACING_CUMUL))
        plt.gca().yaxis.grid()
        plt.tight_layout()
        plt.savefig(plot_filename, format='png')
        plt.close()

        # line plot recording hours
        rec_hours_series = self.time_series['rec_hours_series']
        plot_filename = os.path.join(self.media_dir, 'images', 'rec_hours.png')

        plt.plot(date_series, rec_hours_series, label="Recording hours")
        target_rec_hours_series = np.ones(len(rec_hours_series)) * 22
        plt.plot(date_series, target_rec_hours_series, label="Target")
        plt.gca().xaxis.set_major_formatter(TICK_DATE_FORMAT)
        plt.xticks(rotation=70)
        plt.gca().yaxis.grid()
        plt.legend()
        plt.tight_layout()
        plt.savefig(plot_filename, format='png')
        plt.close()

        # line plot target production and app
        ctm_series = [val[0] for val in self.prod_series['ctm_series']]
        plot_filename = os.path.join(self.media_dir, 'images', 'ctm.png')

        plt.plot(date_series, total_sp_series, label="APP")
        plt.plot(date_series, ctm_series, label="CTM")
        plt.gca().xaxis.set_major_formatter(TICK_DATE_FORMAT)
        plt.xticks(rotation=70)
        plt.gca().yaxis.grid()
        plt.legend()
        plt.tight_layout()
        plt.savefig(plot_filename, format='png')
        plt.close()

        # line plot production / target production ratio
        plot_filename = os.path.join(self.media_dir, 'images', 'app_ctm.png')

        app_ctm_series = np.array([val[1] for val in self.prod_series['ctm_series']])
        target_series = np.ones(len(app_ctm_series))
        plt.plot(date_series, target_series, label="Target")
        plt.plot(date_series, app_ctm_series, label="Prod/Target")
        plt.gca().yaxis.set_major_formatter(mtick.PercentFormatter(xmax=1))
        plt.yticks([0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5])
        plt.gca().yaxis.grid()
        plt.gca().xaxis.set_major_formatter(TICK_DATE_FORMAT)
        plt.xticks(rotation=70)
        plt.legend()
        plt.tight_layout()
        plt.savefig(plot_filename, format='png')
        plt.close()

    @timed(logger, print_log=True)
    def calc_totals(self, daily):
        if not daily:
            return {}, {}, {}

        # get time breakdown stats
        day_times = self.calc_day_time_totals(daily)
        month_times = self.calc_month_time_totals(daily)
        proj_times, self.time_series = self.calc_proj_time_totals(daily)

        # TODO make loop over source types
        # get the production stats
        day_prod = self.calc_day_prod_totals(daily, SOURCETYPE_NAME)
        day_ctm = self.calc_ctm(daily, SOURCETYPE_NAME, day_prod['tcf'])

        month_prod = self.calc_month_prod_totals(daily, SOURCETYPE_NAME)
        month_ctm = self.calc_ctm(daily, SOURCETYPE_NAME, month_prod['month_tcf'])

        proj_prod, self.prod_series = self.calc_proj_prod_totals(daily, SOURCETYPE_NAME)
        proj_ctm = self.calc_ctm(daily, SOURCETYPE_NAME, proj_prod['proj_tcf'])

        day_ctm *= (day_times['total_time'] - day_times['standby']) / 24
        day_app_ctm = calc_ratio(day_prod['total_sp'], day_ctm)
        day_rate = self.calc_rate_current(
            daily, day_app_ctm, day_times['total_time'], day_times['standby']
        )
        day_prod['ctm'] = (day_ctm, day_app_ctm, day_rate)

        month_ctm *= (month_times['month_total_time'] - month_times['month_standby']) / 24
        month_app_ctm = calc_ratio(month_prod['month_total'], month_ctm)
        month_rate = self.calc_rate_current(
            daily, month_app_ctm,
            month_times['month_total_time'], month_times['month_standby']
        )
        month_prod['month_ctm'] = (month_ctm, month_app_ctm, month_rate)

        proj_ctm *= (proj_times['proj_total_time'] - proj_times['proj_standby']) / 24
        proj_app_ctm = calc_ratio(proj_prod['proj_total'], proj_ctm)
        proj_rate = self.calc_rate_current(
            daily, proj_app_ctm,
            proj_times['proj_total_time'], proj_times['proj_standby']
        )
        proj_prod['proj_ctm'] = (proj_ctm, proj_app_ctm, proj_rate)

        ctm_series = self.calc_ctm_series(
            daily, SOURCETYPE_NAME, self.prod_series['tcf_series'])
        ops_time_series = (
            self.time_series['total_time_series'] - self.time_series['standby_series'])
        ctm_series = ctm_series * ops_time_series / 24
        total_sp_series = np.array(
            [sum(terrain) for terrain in self.prod_series['terrain_series']])
        app_ctm_series = np.array(
            [calc_ratio(total_sp, ctm)
             for total_sp, ctm in zip(total_sp_series, ctm_series)])
        self.prod_series['ctm_series'] = np.array(list(zip(ctm_series, app_ctm_series)))

        # get the HSE stats
        day_hse = self.day_hse_totals(daily)
        month_hse = self.month_hse_totals(daily)
        proj_hse = self.proj_hse_totals(daily)

        prod_total = {**day_prod, **month_prod, **proj_prod}
        times_total = {**day_times, **month_times, **proj_times}
        hse_total = {**day_hse, **month_hse, **proj_hse}

        return prod_total, times_total, hse_total

    @timed(logger, print_log=True)
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
        self, daily, period: int, planned: int, complete: float) -> str:
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
