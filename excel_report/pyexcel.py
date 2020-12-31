''' writing excel with python
'''
from openpyxl import Workbook

workbook = Workbook()
sheet = workbook.active

sheet['a1'] = "hello"
sheet['a2'] = 'world'

workbook.save(filename='hello_world.xlsx')
