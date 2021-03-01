''' module to generate excel version of mpr
'''
import calendar
import numpy as np
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font
from openpyxl.utils.dataframe import dataframe_to_rows
from daily_report.report_backend import ReportInterface
from seismicreport.utils.utils_excel import (
    set_vertical_cells, set_horizontal_cells, format_vertical, format_horizontal,
    set_column_widths, set_color, save_excel,
)
from seismicreport.vars import (
    CONTRACT, source_prod_schema, time_breakdown_schema, hse_weather_schema
)

fontname = 'Tahoma'
font_large_bold = Font(name=fontname, bold=True, size=11)
font_normal = Font(name=fontname, size=9)
font_bold = Font(name=fontname, bold=True, size=9)
lightblue = 'D8EFF8'

#pylint: disable=line-too-long


class ExcelMprReport():
    ''' class to create excel mpr report
    '''
    def __init__(self, day):
        self.day = day
        self.sourcetype_names = [
            stype.sourcetype_name for stype in self.day.project.sourcetypes.all()
        ]
        self.wb = Workbook()
        self.wb.remove_sheet(self.wb.get_sheet_by_name('Sheet'))
        self.ws = self.wb.create_sheet('MPR')
        self.ws.sheet_view.showGridLines = False

        self.ws_stypes = {}
        if len(self.sourcetype_names) > 1:
            for stype_name in self.sourcetype_names:
                self.ws_stypes[stype_name] = self.wb.create_sheet(stype_name)
                self.ws_stypes[stype_name].sheet_view.showGridLines = False

        self.wp = self.wb.create_sheet('Project')
        self.wp.sheet_view.showGridLines = False

        r_iface = ReportInterface('')
        self.prod_total, self.times_total, _, _ = r_iface.calc_totals(self.day)
        (
            self.prod_series_by_type, self.prod_series,
            self.time_series, _, self.hse_series
        ) = r_iface.series

    def get_parameters(self, prod_total, times_total, sourcetype):
        if sourcetype:
            sweep = sourcetype.mpr_sweep_length
            vibes = sourcetype.mpr_vibes
            moveup = sourcetype.mpr_moveup
            rechours = sourcetype.mpr_rec_hours

        else:
            sweep = 'mixed sourcetypes'
            vibes = ''
            moveup = ''
            rechours = ''

        params = {}
        params['project'] = self.day.project.project_name
        params['crew'] = self.day.project.crew_name
        params['month'] = self.day.production_date.month
        params['year'] = self.day.production_date.year
        params['days'] = self.day.production_date.day
        params['sweep'] = sweep
        params['vibes'] = vibes
        params['moveup'] = moveup
        params['rechours'] = rechours
        params['production_days'] = (
            self.day.production_date - self.day.project.planned_start_date).days + 1
        params['TCF'] = self.prod_total['month_tcf']
        params['CTM'] = self.prod_total['month_ctm']
        params['APPCTM'] = self.prod_total['month_appctm']
        params['RATE'] = self.prod_total['month_rate']
        params['APP'] = self.prod_total['month_total']
        params['stby_days'] = self.times_total['month_standby'] / 24
        return params

    def collate_mpr_data(self, prod_series, time_series, hse_series):

        prod_keys = ['date_series']
        prod_keys += [f'{key[:5]}_series' for key in source_prod_schema]
        prod_keys += ['total_sp_series', 'tcf_series', 'ctm_series', 'appctm_series']
        p_series = {f'{key[:-7]}':prod_series[key] for key in prod_keys}

        time_keys = [f'{key}_series' for key in time_breakdown_schema]
        time_keys += [
            'ops_series', 'standby_series', 'downtime_series', 'total_time_series']
        t_series = {f'{key[:-7]}': time_series[key] for key in time_keys}
        proj_df = pd.DataFrame({**p_series, **t_series})

        if hse_series:
            hse_keys = ['date_series']
            hse_keys += [f'{key}_series' for key in hse_weather_schema[:12]]
            h_series = {f'{key[:-7]}': hse_series[key] for key in hse_keys}
            hse_df = pd.DataFrame(h_series)
            proj_df = proj_df.merge(hse_df, how='left', left_on='date', right_on='date')


        proj_df['date'] = pd.to_datetime(proj_df['date'])

        return proj_df

    def create_tab_mpr(self, ws, params, proj_df):
        ''' method to create excel mpr report tab
        '''
        # set the titles
        ws.merge_cells('I1:M1')
        ws['I1'].value = 'Production Record and Bonus Calculator'
        ws['I1'].font = font_large_bold

        for r in range(2, 11):
            ws.merge_cells(f'A{r}:C{r}')
            ws.merge_cells(f'D{r}:E{r}')

        monthyear = f'{calendar.month_name[params["month"]]}, {params["year"]}'

        set_vertical_cells(ws, 'A2', ['Contract'], font_bold, Alignment(horizontal='left'))
        set_vertical_cells(ws, 'A3', ['Project'], font_bold, Alignment(horizontal='left'))
        set_vertical_cells(ws, 'A4', ['Crew'], font_bold, Alignment(horizontal='left'))
        set_vertical_cells(ws, 'A5', ['Month, Year'], font_bold, Alignment(horizontal='left'))
        set_vertical_cells(ws, 'A6', ['Days in month'], font_bold, Alignment(horizontal='left'))
        set_vertical_cells(ws, 'A7', ['Sweep length'], font_bold, Alignment(horizontal='left'))
        set_vertical_cells(ws, 'A8', ['Contractual vibrators'], font_bold, Alignment(horizontal='left'))
        set_vertical_cells(ws, 'A9', ['Contractual recording hours'], font_bold, Alignment(horizontal='left'))
        set_vertical_cells(ws, 'A10', ['Move up time'], font_bold, Alignment(horizontal='left'))

        set_vertical_cells(ws, 'D2', [CONTRACT], font_normal, Alignment(horizontal='right'))
        set_vertical_cells(ws, 'D3', [f'{params["project"]}'], font_normal, Alignment(horizontal='right'))
        set_vertical_cells(ws, 'D4', [f'{params["crew"]}'], font_normal, Alignment(horizontal='right'))
        set_vertical_cells(ws, 'D5', [monthyear], font_normal, Alignment(horizontal='right'))
        set_vertical_cells(ws, 'D6', [params['days']], font_normal, Alignment(horizontal='right'))
        set_vertical_cells(ws, 'D7', [params['sweep']], font_normal, Alignment(horizontal='right'))
        set_vertical_cells(ws, 'D8', [params['vibes']], font_normal, Alignment(horizontal='right'))
        set_vertical_cells(ws, 'D9', [params['rechours']], font_normal, Alignment(horizontal='right'))
        set_vertical_cells(ws, 'D10', [params['moveup']], font_normal, Alignment(horizontal='right'))

        for r in range(5, 11):
            ws.merge_cells(f'H{r}:J{r}')
            ws.merge_cells(f'K{r}:L{r}')

        set_vertical_cells(ws, 'H5', ['Terrain correction factor'], font_bold, Alignment(horizontal='left'))
        set_vertical_cells(ws, 'H6', ['CTM month'], font_bold, Alignment(horizontal='left'))
        set_vertical_cells(ws, 'H7', ['APP month'], font_bold, Alignment(horizontal='left'))
        set_vertical_cells(ws, 'H8', ['APP / CTM'], font_bold, Alignment(horizontal='left'))
        set_vertical_cells(ws, 'H9', ['Standby days for month'], font_bold, Alignment(horizontal='left'))
        set_vertical_cells(ws, 'H10', ['Effective month rate'], font_bold, Alignment(horizontal='left'))

        set_vertical_cells(ws, 'K5', [params['TCF']], font_normal, Alignment(horizontal='right'))
        set_vertical_cells(ws, 'K6', [params['CTM']], font_normal, Alignment(horizontal='right'))
        set_vertical_cells(ws, 'K7', [params['APP']], font_normal, Alignment(horizontal='right'))
        set_vertical_cells(ws, 'K8', [params['APPCTM']], font_normal, Alignment(horizontal='right'))
        set_vertical_cells(ws, 'K9', [params['stby_days']], font_normal, Alignment(horizontal='right'))
        set_vertical_cells(ws, 'K10', [params['RATE']], font_normal, Alignment(horizontal='right'))

        # and some formatting ...
        for r in [5, 10]:
            ws[f'K{r}'].number_format = '0.00%'

        for r in [8, 9]:
            ws[f'K{r}'].number_format = '0.000'

        for r in [6, 7]:
            ws[f'K{r}'].number_format = '#,##0'

        # set the table
        header = [
            'Date', 'Prod. day', 'Flat', 'Rough', 'Facilities', 'Dunes', 'Sabkha',
            'Skips', 'Total VP', 'Cum VPs', 'Rec. hours', 'Other Ops', 'Ops time',
            'Standby', 'Down', 'Flat', 'Rough', 'Facilities', 'Dunes', 'Sabkha',
            'TCF', 'CTM', 'APP/CTM', 'PAD time',
        ]
        set_horizontal_cells(ws, 'A12', header, font_bold,
            Alignment(horizontal='center', wrap_text=True, vertical='top'))
        set_color(ws, 'A12:X12', color=lightblue)

        m_df = proj_df[
            (proj_df.date.dt.month == params['month']) &
            (proj_df.date.dt.year == params['year'])]

        dates = m_df.date.dt.strftime('%d-%b-%y').to_list()
        m_day = params['days'] - 1
        prod_days = [
            params['production_days'] - m_day + d for d in range(m_day + 1)]

        vp_type = {}
        vp_typesum = {}
        vp_type['total'] = np.array(m_df.total_sp.to_list(), dtype=float)
        vp_type['cumtotal'] = np.cumsum(vp_type['total'])
        vp_typesum['total'] = np.sum(vp_type['total'])
        vp_type['ctm'] = np.array(m_df.ctm.to_list(), dtype=float)
        vp_typesum['ctm'] = np.nansum(vp_type['ctm'])

        # calculate the vp terrain distributions and sums
        vp_dist = {}
        vp_distsum = {}
        for col in ['sp_t1', 'sp_t2', 'sp_t3', 'sp_t4', 'sp_t5', 'skips']:
            vp_type[col] = np.array(m_df[col].to_list(), dtype=float)
            vp_dist[col] = np.divide(
                vp_type[col], vp_type['total'], out=np.zeros_like(
                    vp_type[col]), where=vp_type['total']!=0)
            vp_typesum[col] = np.sum(vp_type[col])

            if vp_typesum['total'] > 0:
                vp_distsum[col] = vp_typesum[col] / vp_typesum['total']

            else:
                vp_distsum[col] = 0

        # calculate times and sums
        tm_type = {}
        tm_typesum = {}
        for col in ['rec_hours', 'ops', 'standby', 'downtime']:
            tm_type[col] = np.array(m_df[col].to_list())
            tm_typesum[col] = np.sum(tm_type[col])

        tm_type['other_ops'] = tm_type['ops'] - tm_type['rec_hours']
        tm_typesum['other_ops'] = np.sum(tm_type['other_ops'])

        if params['rechours']:
            padtime = tm_type['rec_hours'] / params['rechours']
            padtimesum = (
                tm_typesum['rec_hours'] / (params['rechours'] * params['days']))

        else:
            padtime = tm_type['rec_hours'] * 0
            padtimesum = 0

        set_vertical_cells(ws, 'A13', dates, font_normal, Alignment())
        set_vertical_cells(ws, 'B13', prod_days, font_normal, Alignment())
        set_vertical_cells(ws, 'C13', vp_type['sp_t1'], font_normal, Alignment())
        set_vertical_cells(ws, 'D13', vp_type['sp_t2'], font_normal, Alignment())
        set_vertical_cells(ws, 'E13', vp_type['sp_t3'], font_normal, Alignment())
        set_vertical_cells(ws, 'F13', vp_type['sp_t4'], font_normal, Alignment())
        set_vertical_cells(ws, 'G13', vp_type['sp_t5'], font_normal, Alignment())
        set_vertical_cells(ws, 'H13', vp_type['skips'], font_normal, Alignment())
        set_vertical_cells(ws, 'I13', vp_type['total'], font_normal, Alignment())
        set_vertical_cells(ws, 'J13', vp_type['cumtotal'], font_normal, Alignment())
        set_vertical_cells(ws, 'K13', tm_type['rec_hours'], font_normal, Alignment())
        set_vertical_cells(ws, 'L13', tm_type['other_ops'], font_normal, Alignment())
        set_vertical_cells(ws, 'M13', tm_type['ops'], font_normal, Alignment())
        set_vertical_cells(ws, 'N13', tm_type['standby'], font_normal, Alignment())
        set_vertical_cells(ws, 'O13', tm_type['downtime'], font_normal, Alignment())
        set_vertical_cells(ws, 'P13', vp_dist['sp_t1'], font_normal, Alignment())
        set_vertical_cells(ws, 'Q13', vp_dist['sp_t2'], font_normal, Alignment())
        set_vertical_cells(ws, 'R13', vp_dist['sp_t3'], font_normal, Alignment())
        set_vertical_cells(ws, 'S13', vp_dist['sp_t4'], font_normal, Alignment())
        set_vertical_cells(ws, 'T13', vp_dist['sp_t5'], font_normal, Alignment())
        set_vertical_cells(ws, 'U13', m_df.tcf.to_list(), font_normal, Alignment())
        set_vertical_cells(ws, 'V13', vp_type['ctm'], font_normal, Alignment())
        set_vertical_cells(ws, 'W13', m_df.appctm.to_list(), font_normal, Alignment())
        set_vertical_cells(ws, 'X13', padtime, font_normal, Alignment())

        # and some formating of columns
        for c in ['K', 'L', 'M', 'N', 'O']:
            format_vertical(ws, f'{c}13:{c}100', '0.00')
        for c in ['P', 'Q', 'R', 'S', 'T', 'U', 'W', 'X']:
            format_vertical(ws, f'{c}13:{c}100', '0.0%')
        for c in ['I', 'J', 'V']:
            format_vertical(ws, f'{c}13:{c}100', '#,##0')

        # add row with the sums
        row_sum = [
            'Total', params['days'], vp_typesum['sp_t1'], vp_typesum['sp_t2'],
            vp_typesum['sp_t3'], vp_typesum['sp_t4'], vp_typesum['sp_t5'],
            vp_typesum['skips'], vp_typesum['total'], '', tm_typesum['rec_hours'],
            tm_typesum['other_ops'], tm_typesum['ops'], tm_typesum['standby'],
            tm_typesum['downtime'], vp_distsum['sp_t1'], vp_distsum['sp_t2'],
            vp_distsum['sp_t3'], vp_distsum['sp_t4'], vp_distsum['sp_t5'],
            params['TCF'], params['CTM'], params['APPCTM'], padtimesum,
        ]
        set_horizontal_cells(ws, f'A{13+params["days"]}', row_sum, font_bold, Alignment())
        format_horizontal(ws, f'C{13+params["days"]}:H{13+params["days"]}', '#,##0')
        set_color(ws, f'A{13+params["days"]}:X{13+params["days"]}', color=lightblue)

    def create_tab_proj(self, proj_df):
        set_column_widths(self.wp, 'A', [12.5])
        rows = dataframe_to_rows(proj_df, index=False, header=True)
        self.wp.freeze_panes = 'B2'

        for r_id, row in enumerate(rows, 1):
            for c_id, value in enumerate(row, 1):
                self.wp.cell(row=r_id, column=c_id, value=value)

    def create_mprreport(self):
        main_proj_df = self.collate_mpr_data(
            self.prod_series, self.time_series, self.hse_series
        )
        stype = None
        if self.ws_stypes:
            params = self.get_parameters(self.prod_total, self.times_total, stype)
            self.create_tab_mpr(self.ws, params, main_proj_df)

            for stype_name in self.sourcetype_names:
                stype = self.day.project.sourcetypes.get(
                    sourcetype_name=stype_name
                )
                params = self.get_parameters(self.prod_total, self.times_total, stype)
                proj_df = self.collate_mpr_data(
                    self.prod_series_by_type[stype_name], self.time_series,
                    self.hse_series
                )
                self.create_tab_mpr(self.ws_stypes[stype_name], params, proj_df)

        else:
            stype = self.day.project.sourcetypes.all()[0]
            params = self.get_parameters(self.prod_total, self.times_total, stype)
            self.create_tab_mpr(self.ws, params, main_proj_df)


        self.create_tab_proj(main_proj_df)
        return save_excel(self.wb)
