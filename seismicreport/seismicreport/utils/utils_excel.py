
''' module with utilities for excel
'''
import io
import re
from openpyxl.styles import Border, Side


def set_vertical_cells(ws, loc_init: str, values: list, font, alignment):
    # loc_init: format "A0" multiple capital letters followd by multiple numbers
    loc = re.match(r'^([A-Z]+)([0-9]+)$', loc_init)
    row_init = int(loc.group(2))
    col_init = loc.group(1)
    for i, value in enumerate(values):
        loc = col_init + str(row_init + i)
        cell = ws[loc]
        cell.value = value
        cell.font = font
        cell.alignment = alignment


def set_outer_border(ws, cell_range, style='thin'):
    cells =ws[cell_range]
    row = None
    for i, row in enumerate(cells):
        if i == 0:
            for col in row:
                col.border = col.border + Border(top=Side(style=style))

        row[0].border = row[0].border + Border(left=Side(style=style))
        row[-1].border = row[-1].border + Border(right=Side(style=style))

    for col in row:
        col.border = col.border + Border(bottom=Side(style=style))


def save_excel(wb):
    ''' method to save excel data to a BytesIO buffer
    '''
    f_excel = io.BytesIO()
    wb.save(f_excel)
    f_excel.seek(0)
    return f_excel
