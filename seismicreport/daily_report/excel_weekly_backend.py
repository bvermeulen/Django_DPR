''' writing excel with python
'''
from pathlib import Path
from openpyxl import Workbook, drawing
from openpyxl.styles import Border, Side, Alignment, Font, PatternFill
from openpyxl.formatting.rule import CellIsRule
from daily_report.report_backend import ReportInterface
from daily_report.week_backend import WeekInterface
from seismicreport.utils.utils_excel import (
    set_vertical_cells, set_outer_border, save_excel
)
from seismicreport.vars import AVG_PERIOD, NO_DATE_STR, SS_2


class ExcelWeekReport:
    ''' class to create excel week report in CSR format
    '''
    def __init__(self, report_data, media_root, static_root):
        self.media_root = Path(media_root)
        self.static_root = Path(static_root)
        self.wb = Workbook()
        self.ws = self.wb.active
        self.ws.sheet_view.showGridLines = False
        self.parse_data(report_data)

    def parse_data(self, report_data):
        self.report_date = report_data['report_date']
        self.project_table = report_data['project_table']
        self.daily_table = report_data['daily_table']
        self.recvr_table = report_data['receiver_table']
        self.csr_table = report_data['csr_table']
        self.proj_stats_table = report_data['proj_stats_table']
        self.block_stats_table = report_data['block_stats_table']
        self.hse_stats_table = report_data['hse_stats_table']
        self.csr_comment_table = report_data['csr_comment_table']

    def create_weeklyreport(self):
        ''' method to create excel daily report
        '''
        fontname = 'Tahoma'
        red = '00FF0000'
        green = '0000FF00'
        font_large_bold = Font(name=fontname, bold=True, size=11)
        font_normal = Font(name=fontname, size=9)
        font_bold = Font(name=fontname, bold=True, size=9)

        self.ws.column_dimensions['A'].width = 0.94
        self.ws.column_dimensions['B'].width = 0.75
        self.ws.column_dimensions['C'].width = 11.78
        self.ws.column_dimensions['D'].width = 10.89
        self.ws.column_dimensions['E'].width = 20.89
        self.ws.column_dimensions['F'].width = 0.56
        self.ws.column_dimensions['G'].width = 0.75
        self.ws.column_dimensions['H'].width = 14.11
        self.ws.column_dimensions['I'].width = 10.56
        self.ws.column_dimensions['J'].hidden = True
        self.ws.column_dimensions['K'].width = 13.22
        self.ws.column_dimensions['L'].width = 11.00

        # set logo
        img_logo = drawing.image.Image(self.static_root / 'img/client_icon.png')
        img_logo.width = 75
        img_logo.height = 75
        self.ws.add_image(img_logo, 'C4')

        # set title
        self.ws.merge_cells('B2:K2')
        self.ws['B2'].value = 'CSR DAILY REPORT'
        self.ws['B2'].alignment = Alignment(horizontal='center')
        self.ws['B2'].font = font_large_bold

        # set date
        self.ws.merge_cells('H3:I3')
        self.ws.merge_cells('K3:L3')
        set_vertical_cells(
            self.ws, 'H3', ['DATE'], font_large_bold, Alignment(horizontal='right'))
        set_vertical_cells(
            self.ws, 'K3', [self.report_date], font_large_bold, Alignment())
        self.ws['K3'].font = Font(name=fontname, bold=True, size=11, color=red)

        # set borders
        set_outer_border(self.ws, 'B2:L46')
        set_outer_border(self.ws, 'B2:L2')
        set_outer_border(self.ws, 'B3:I15')
        set_outer_border(self.ws, 'H4:I11')
        set_outer_border(self.ws, 'H12:I15')
        set_outer_border(self.ws, 'K4:L9')
        set_outer_border(self.ws, 'K4:L4')
        set_outer_border(self.ws, 'K10:L15')
        set_outer_border(self.ws, 'K11:L11')
        set_outer_border(self.ws, 'K17:L26')
        set_outer_border(self.ws, 'K17:L17')
        set_outer_border(self.ws, 'B16:I26')
        self.ws['I3'].border = Border(top=Side(style='thin'), bottom=Side(style='thin'))

        return save_excel(self.wb)


def collate_excel_weeklyreport_data(day):
    r_iface = ReportInterface('')
    w_iface = WeekInterface('')
    project = day.project

    totals_prod, totals_time, totals_hse = r_iface.calc_totals(day)
    totals_rcvr = r_iface.calc_receiver_totals(day)
    days, weeks = w_iface.collate_weekdata(day)

    report_data = {}
    report_data['report_date'] = day.production_date.strftime('%#d %b %Y')
    report_data['author'] = {}

    proj_start = (
        project.planned_start_date.strftime('%#d %b %Y')
        if project.planned_start_date else NO_DATE_STR
    )

    report_data['project_table'] = {
        'Project': project.project_name,
        'Project VPs': project.planned_vp,
        f'Area (km{SS_2})': project.planned_area,
        'Proj. Start': proj_start,
        'Crew': project.crew_name,
    }

    # proj_stats
    proj_total = totals_prod['proj_total']
    proj_skips = totals_prod['proj_skips']
    if project.planned_vp > 0:
        proj_complete = (proj_total + proj_skips) / project.planned_vp

    else:
        proj_complete = 0

    report_data['proj_stats_table'] = {
        'Recorded VPs': proj_total,
        f'Area (km{SS_2})': project.planned_area * proj_complete,
        'Skip VPs': proj_skips,
        '% Complete': proj_complete,
        'Est. Complete': r_iface.calc_est_completion_date(
            day, AVG_PERIOD, project.planned_vp, proj_complete),
    }

    report_data['hse_stats_table'] = {
        'LTI': totals_hse['lti'],
        'RWC': totals_hse['rwc'],
        'MTC': totals_hse['mtc'],
        'FAC': totals_hse['fac'],
        'NM/ Incidents': totals_hse['incident_nm'],
        'LSR': totals_hse['lsr_violations'],
        'STOP': totals_hse['stop'],
    }

    report_data['csr_comment_table'] = {
        'Comments': day.csr_comment,
    }

    return report_data
