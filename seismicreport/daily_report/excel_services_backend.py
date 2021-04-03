''' module for creating excel monthly services '''
import calendar
from openpyxl.styles import Alignment, Font
from seismicreport.utils.utils_excel import (
    set_vertical_cells, set_horizontal_cells, format_vertical, format_horizontal,
    set_column_widths, set_color, save_excel,
)
from seismicreport.vars import CONTRACT

fontname = 'Tahoma'
font_large_bold = Font(name=fontname, bold=True, size=11)
font_normal = Font(name=fontname, size=9)
font_bold = Font(name=fontname, bold=True, size=9)
lightblue = 'D8EFF8'

#pylint: disable=line-too-long


class Mixin:

    @staticmethod
    def create_tab_services(ws, day):
        project = day.project
        monthyear = (
            f'{calendar.month_name[day.production_date.month]}, '
            f'{day.production_date.year}'
        )
        # set column widths
        set_column_widths(ws, 'A', [20.0])
        set_column_widths(ws, 'B', [4.0]*31 + [12])

        # set the titles
        ws.merge_cells('P1:T1')
        ws['P1'].value = 'Monthly services'
        ws['P1'].font = font_large_bold

        for r in range(2, 6):
            ws.merge_cells(f'B{r}:E{r}')

        set_vertical_cells(ws, 'A2', ['Contract'], font_bold, Alignment(horizontal='left'))
        set_vertical_cells(ws, 'A3', ['Project'], font_bold, Alignment(horizontal='left'))
        set_vertical_cells(ws, 'A4', ['Crew'], font_bold, Alignment(horizontal='left'))
        set_vertical_cells(ws, 'A5', ['Month, Year'], font_bold, Alignment(horizontal='left'))

        set_vertical_cells(ws, 'B2', [CONTRACT], font_normal, Alignment(horizontal='right'))
        set_vertical_cells(ws, 'B3', [project.project_name], font_normal, Alignment(horizontal='right'))
        set_vertical_cells(ws, 'B4', [project.crew_name], font_normal, Alignment(horizontal='right'))
        set_vertical_cells(ws, 'B5', [monthyear], font_normal, Alignment(horizontal='right'))

        for service in project.services.all():
            print(service)