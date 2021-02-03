''' module to generate excel version of mpr
'''
import numpy as np
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font
from openpyxl.utils.dataframe import dataframe_to_rows
from daily_report.report_backend import ReportInterface
from seismicreport.utils.utils_excel import (
    set_vertical_cells, set_horizontal_cells, format_vertical, format_horizontal,
    conditional_format, set_column_widths, set_border, set_outer_border,
    set_color, save_excel, get_row_column,
)
from seismicreport.utils.utils_funcs import nan_array, get_sourcereceivertype_names
from seismicreport.vars import (
    source_prod_schema, time_breakdown_schema, hse_weather_schema, TCF_table,
)

fontname = 'Tahoma'
font_large_bold = Font(name=fontname, bold=True, size=11)
font_normal = Font(name=fontname, size=9)
font_bold = Font(name=fontname, bold=True, size=9)
red = '00FF0000'
green ='0000FF00'
orange = 'FFA500'
lightblue = 'D8EFF8'
float_hide_zero = '0.00;-0;;@'
int_hide_zero = '#,##0;0;;@'


class ExcelMprReport():
    ''' class to create excel mpr report
    '''
    def __init__(self, day):
        self.day = day
        self.wb = Workbook()
        self.wb.remove_sheet(self.wb.get_sheet_by_name('Sheet'))
        self.ws = self.wb.create_sheet('MPR')
        self.ws.sheet_view.showGridLines = False
        self.wp = self.wb.create_sheet('Project')
        self.wp.sheet_view.showGridLines = False

        self.proj_params = self.get_parameters()
        self.proj_df = self.collate_mpr_data()

    def get_parameters(self):
        sourcetype_name, _ = get_sourcereceivertype_names(self.day)
        sourcetype = self.day.project.sourcetypes.get(sourcetype_name=sourcetype_name)
        params = {}
        params['project'] = self.day.project.project_name
        params['crew'] = self.day.project.crew_name
        params['month'] = self.day.production_date.month
        params['year'] = self.day.production_date.year
        params['days'] = self.day.production_date.day
        params['sweep'] = sourcetype.mpr_sweep_length
        params['vibes'] = sourcetype.mpr_vibes
        params['moveup'] = sourcetype.mpr_moveup
        params['rechours'] = sourcetype.mpr_rec_hours
        params['production_days'] = (
            self.day.production_date - self.day.project.planned_start_date).days + 1
        return params

    def collate_mpr_data(self):
        r_iface = ReportInterface('')
        r_iface.calc_totals(self.day)
        prod_series, time_series, hse_series = r_iface.series
        if not prod_series:
            return

        prod_keys = ['date_series']
        prod_keys += [f'{key[:5]}_series' for key in source_prod_schema]
        prod_keys += ['total_sp_series', 'tcf_series', 'ctmvp_series', 'appctm_series']
        prod_series['ctmvp_series'] = [val[0] for val in prod_series['ctm_series']]
        prod_series['appctm_series'] = [val[1] for val in prod_series['ctm_series']]
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

        return proj_df

    def create_tab_mpr(self):
        ''' method to create excel mpr report tab
        '''
        # set_column_widths(self.wsw, 'A',
        #     [0.94, 0.75, 12.56, 10.22, 19.89, 4.11, 0.81,
        #     11.67, 11.22, 12.56, 11.22, 0.94]
        # )
        header = [
            'Date', 'Prod. day', 'Flat', 'Rough', 'Facilities', 'Dunes', 'Sabkha',
            'Skips', 'Total VP', 'Cum VPs', 'Rec. hours', 'Other Ops', 'Ops time',
            'Standby', 'Down', 'Flat', 'Rough', 'Facilities', 'Dunes', 'Sabkha',
            'TCF', 'CTM', 'APP/CTM', 'PAD time',
        ]
        set_horizontal_cells(self.ws, 'A26', header, font_bold,
            Alignment(horizontal='center', wrap_text=True, vertical='top'))


    def create_tab_proj(self):
        set_column_widths(self.wp, 'A', [12.5])
        rows = dataframe_to_rows(self.proj_df, index=False, header=True)
        self.wp.freeze_panes = 'B2'

        for r_id, row in enumerate(rows, 1):
            for c_id, value in enumerate(row, 1):
                self.wp.cell(row=r_id, column=c_id, value=value)

    def create_mprreport(self):
        self.create_tab_mpr()
        self.create_tab_proj()
        return save_excel(self.wb)
