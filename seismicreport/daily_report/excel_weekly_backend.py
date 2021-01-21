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
        self.wsw = self.wb.create_sheet('CSR_WEEKLY')
        self.wst = self.wb.create_sheet('Times')
        self.wsp = self.wb.create_sheet('Production')
        self.wsw.sheet_view.showGridLines = False
        self.wst.sheet_view.showGridLines = False
        self.wsp.sheet_view.showGridLines = False

        self.parse_data(report_data)

    def parse_data(self, report_data):
        self.report_date = report_data['report_date']
        self.author = report_data['author_table']
        self.comment_table = report_data['comment_table']
        self.proj_table = report_data['project_table']
        self.proj_stats = report_data['proj_stats_table']
        self.hse_stats_week = report_data['hse_stats_week_table']
        self.hse_stats_month = report_data['hse_stats_month_table']
        self.hse_stats_proj = report_data['hse_stats_proj_table']
        self.prod_stats_week = report_data['prod_stats_week_table']
        self.prod_stats_month = report_data['prod_stats_month_table']
        self.prod_stats_proj = report_data['prod_stats_proj_table']
        self.days_prod = report_data['days_prod']
        self.weeks_prod = report_data['weeks_prod']
        self.days_times = report_data['days_times']
        self.weeks_times = report_data['weeks_times']

    def create_weekreport(self):
        ''' method to create excel daily report
        '''
        fontname = 'Tahoma'
        red = '00FF0000'
        green = '0000FF00'
        font_large_bold = Font(name=fontname, bold=True, size=11)
        font_normal = Font(name=fontname, size=9)
        font_bold = Font(name=fontname, bold=True, size=9)

        self.wsw.column_dimensions['A'].width = 0.94
        self.wsw.column_dimensions['B'].width = 0.75
        self.wsw.column_dimensions['C'].width = 12.56
        self.wsw.column_dimensions['D'].width = 10.22
        self.wsw.column_dimensions['E'].width = 19.89
        self.wsw.column_dimensions['F'].width = 4.11
        self.wsw.column_dimensions['G'].width = 0.81
        self.wsw.column_dimensions['H'].width = 11.67
        self.wsw.column_dimensions['I'].width = 11.22
        self.wsw.column_dimensions['J'].hidden = True
        self.wsw.column_dimensions['K'].width = 12.56
        self.wsw.column_dimensions['L'].width = 9.78

        # set logo
        img_logo = drawing.image.Image(self.static_root / 'img/client_icon.png')
        img_logo.width = 75
        img_logo.height = 75
        self.wsw.add_image(img_logo, 'C4')

        # set title
        self.wsw.merge_cells('B2:L2')
        self.wsw['B2'].value = 'CSR WEEKLY REPORT'
        self.wsw['B2'].alignment = Alignment(horizontal='center')
        self.wsw['B2'].font = font_large_bold

        # set date
        self.wsw.merge_cells('H3:I3')
        self.wsw.merge_cells('K3:L3')
        set_vertical_cells(
            self.wsw, 'H3', ['DATE'], font_large_bold, Alignment(horizontal='right'))
        set_vertical_cells(
            self.wsw, 'K3', [self.report_date], font_large_bold, Alignment())
        self.wsw['K3'].font = Font(name=fontname, bold=True, size=11, color=red)

        # set author
        self.wsw.merge_cells('H4:I4')
        self.wsw.merge_cells('H5:I5')
        set_vertical_cells(self.wsw, 'H4', [k for k in self.author], font_bold,
            Alignment(horizontal='center'))
        set_vertical_cells(self.wsw, 'H5', [v for v in self.author.values()], font_normal,
            Alignment(horizontal='center'))

        # set borders
        # set_outer_border(self.ws, 'B2:L46')
        # set_outer_border(self.ws, 'B2:L2')
        # set_outer_border(self.ws, 'B3:I15')
        # set_outer_border(self.ws, 'H4:I11')
        # set_outer_border(self.ws, 'H12:I15')
        # set_outer_border(self.ws, 'K4:L9')
        # set_outer_border(self.ws, 'K4:L4')
        # set_outer_border(self.ws, 'K10:L15')
        # set_outer_border(self.ws, 'K11:L11')
        # set_outer_border(self.ws, 'K17:L26')
        # set_outer_border(self.ws, 'K17:L17')
        # set_outer_border(self.ws, 'B16:I26')
        # self.ws['I3'].border = Border(top=Side(style='thin'), bottom=Side(style='thin'))

        return save_excel(self.wb)


def collate_excel_weekreport_data(day):
    r_iface = ReportInterface('')
    w_iface = WeekInterface('')
    project = day.project

    report_data = {}
    totals_prod, totals_time, totals_hse = r_iface.calc_totals(day)
    days, weeks = w_iface.collate_weekdata(day)

    report_data['report_date'] = day.production_date.strftime('%#d %b %Y')

    # CSR author and comment
    if _week:=day.project.weeklies.filter(week_report_date=day.production_date):
        week = _week.first()
        try:
            author = week.author.name
        except AttributeError:
            author = ''
        report_data['author_table'] = {'CSR': author}
        report_data['comment_table'] = {'Comments': week.csr_week_comment}

    else:
        report_data['author_table'] = {'CSR': ''}
        report_data['comment_table'] = {'Comments': ''}

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

    # hse_stats
    for period in ['week', 'month', 'proj']:
        report_data[f'hse_stats_{period}_table'] = {
            'LTI': totals_hse[f'{period}_lti'],
            'RWC': totals_hse[f'{period}_rwc'],
            'MTC': totals_hse[f'{period}_mtc'],
            'FAC': totals_hse[f'{period}_fac'],
            'NM/ Incidents': totals_hse[f'{period}_incident_nm'],
            'LSR': totals_hse[f'{period}_lsr_violations'],
            'STOP Cards': totals_hse[f'{period}_stop'],
            'Drills': totals_hse[f'{period}_drills'],
            'Audits': totals_hse[f'{period}_audits'],
            'Medevac': totals_hse[f'{period}_medevac'],
        }

    # prod stats
    for period in ['week', 'month', 'proj']:
        report_data[f'prod_stats_{period}_table'] = {
            'Total VPs': totals_prod[f'{period}_total'],
            'Target VPS': totals_prod[f'{period}_ctm'][0],
            '% Target': totals_prod[f'{period}_ctm'][1],
            'Rec. Hrs': totals_time[f'{period}_rec_time'],
            'Standby Hrs': totals_time[f'{period}_standby'],
            'Avg VPs/day': totals_prod[f'{period}_avg'],
            'Down Hrs': totals_time[f'{period}_downtime'],
            'Skip VPs': totals_prod[f'{period}_skips'],
            '% Skips': totals_prod[f'{period}_perc_skips'],
        }

    # days prod stats
    report_data['days_prod'] = {
        'header':['Day', 'VPs', 'Rec time', 'VP/ hr', 'Skips',
                  'Layout', 'Pickup', 'QC field', 'QC camp', 'Upload']
    }

    for key, day in reversed(days.items()):
        report_data['days_prod'][key] = [
            day['date'].strftime('%d-%b-%Y'),
            day['prod']['total_sp'],
            day['times']['rec_time'],
            day['prod']['vp_hour'],
            day['prod']['skips'],
            day['rcvr']['layout'],
            day['rcvr']['pickup'],
            day['rcvr']['qc_field'],
            day['rcvr']['qc_camp'],
            day['rcvr']['upload'],
        ]

    report_data['weeks_prod'] = {
        'header':['Week', 'VPs', 'Rec time', 'VP/ hr', 'Skips',
                  'Layout', 'Pickup', 'QC field', 'QC camp', 'Upload']
    }

    # weeks prod stats
    for key, wk in weeks.items():
        print(wk['rcvr'])
        report_data['weeks_prod'][key] = [
            (wk['dates'][0].strftime('%d-%b-%Y') + ' ' +
             wk['dates'][1].strftime('%d-%b-%Y')),
            wk['prod']['week_total'],
            wk['times']['week_rec_time'],
            wk['prod']['week_vp_hour'],
            wk['prod']['week_skips'],
            wk['rcvr']['week_layout'],
            wk['rcvr']['week_pickup'],
            wk['rcvr']['week_qc_field'],
            wk['rcvr']['week_qc_camp'],
            wk['rcvr']['week_upload'],
        ]

 # days times stats
    report_data['days_times'] = {
        'header':['Day', 'Recording','Rec move', 'Logistics', 'WOS', 'WOL',
        'Shift change', 'Company suspension', 'Company requested tests',
        'Beyond contractor control', 'Camp move', 'Line faults', 'Inst. faults',
        'Vib faults', 'Incidents', 'Holiday', 'Further recovery', 'Other DT',
        'Ops time', 'Standby', 'Downtime',]
    }

    for key, wk in reversed(days.items()):
        report_data['days_times'][key] = [
            day['date'].strftime('%d-%b-%Y'),
            day['times']['rec_time'],
            day['times']['rec_moveup'],
            day['times']['logistics'],
            day['times']['wait_source'],
            day['times']['wait_layout'],
            day['times']['wait_shift_change'],
            day['times']['company_suspension'],
            day['times']['company_tests'],
            day['times']['beyond_control'],
            day['times']['camp_move'],
            day['times']['line_fault'],
            day['times']['instrument_fault'],
            day['times']['vibrator_fault'],
            day['times']['incident'],
            day['times']['holiday'],
            day['times']['recovering'],
            day['times']['other_downtime'],
            day['times']['ops_time'],
            day['times']['standby'],
            day['times']['downtime'],

        ]

    #weeks times stat
    report_data['weeks_times'] = {
        'header':['Day', 'Recording','Rec move', 'Logistics', 'WOS', 'WOL',
        'Shift change', 'Company suspension', 'Company requested tests',
        'Beyond contractor control', 'Camp move', 'Line faults', 'Inst. faults',
        'Vib faults', 'Incidents', 'Holiday', 'Further recovery', 'Other DT',
        'Ops time', 'Standby', 'Downtime',]
    }

    for key, wk in weeks.items():
        report_data['weeks_times'][key] = [
            (wk['dates'][0].strftime('%d-%b-%Y') + ' ' +
             wk['dates'][1].strftime('%d-%b-%Y')),
            wk['times']['week_rec_time'],
            wk['times']['week_rec_moveup'],
            wk['times']['week_logistics'],
            wk['times']['week_wait_source'],
            wk['times']['week_wait_layout'],
            wk['times']['week_wait_shift_change'],
            wk['times']['week_company_suspension'],
            wk['times']['week_company_tests'],
            wk['times']['week_beyond_control'],
            wk['times']['week_camp_move'],
            wk['times']['week_line_fault'],
            wk['times']['week_instrument_fault'],
            wk['times']['week_vibrator_fault'],
            wk['times']['week_incident'],
            wk['times']['week_holiday'],
            wk['times']['week_recovering'],
            wk['times']['week_other_downtime'],
            wk['times']['week_ops_time'],
            wk['times']['week_standby'],
            wk['times']['week_downtime'],
        ]

    return report_data
