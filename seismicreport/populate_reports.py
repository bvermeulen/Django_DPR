# populate reports
#pylint: disable=wrong-import-position

import os
from itertools import islice
import numpy as np
import pandas as pd
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'seismicreport.settings')
django.setup()
from django.db.utils import IntegrityError

from daily_report.models.daily_models import Daily, SourceProduction, TimeBreakdown
from daily_report.models.project_models import Project
from seismicreport.vars import SOURCETYPE_NAME

report_filename = r'CSR-MS-NatihWAZ.xlsx'
project_name = 'NatihWAZ'
months = ['Mar-2019', 'Apr-2019', 'May-2019', 'Jun-2019', 'Jul-2019', 'Aug-2019',
          'Sep-2019', 'Oct-2019', 'Nov-2019', 'Dec-2019', 'Jan-2020',]

MPR_table = {
    'date': 1,
    'sp_t1': 3,
    'sp_t2': 4,
    'sp_t3': 5,
    'sp_t4': 6,
    'sp_t5': 7,
    'skips': 26,
    'rec_hours': 10,
    'logistics': 11,
    'beyond_contractor_control': 13,
    'other_dt': 14,
    'front_crew': 20,
    'back_crew': 21,
}


def get_value(row_df, kw):
    if kw not in MPR_table:
        return np.nan

    column = MPR_table[kw]
    value = row_df[1:][0][column]
    if pd.isnull(value):
        value = np.nan
    return value


def populate_report(project, row_df):
    ''' populates db with values from theMPR file
        MPR file is an excel file with fields according
        the MPR_table
    '''
    production_date = get_value(row_df, 'date')

    # check if date is correct format
    try:
        production_date.strftime('%Y-%m-%d')

    except (ValueError, AttributeError):
        return None

    # create/ update day values
    try:
        day = Daily.objects.create(
            production_date=production_date,
            project=project)

    except IntegrityError:
        day = Daily.objects.get(
            production_date=production_date,
            project=project)

    # create/ update vp production values
    try:
        prod = SourceProduction.objects.create(
            daily=day,
            sourcetype=day.project.sourcetypes.get(
                sourcetype_name=SOURCETYPE_NAME)
        )

    except IntegrityError:
        prod = SourceProduction.objects.get(
            daily=day,
            sourcetype=day.project.sourcetypes.get(
                sourcetype_name=SOURCETYPE_NAME)
        )

    prod.sp_t1_flat = int(
        np.nan_to_num(get_value(row_df, 'sp_t1')))
    prod.sp_t2_rough = int(
        np.nan_to_num(get_value(row_df, 'sp_t2')))
    prod.sp_t3_facilities = int(
        np.nan_to_num(get_value(row_df, 'sp_t3')))
    prod.sp_t4_dunes = int(
        np.nan_to_num(get_value(row_df, 'sp_t4')))
    prod.sp_t5_sabkha = int(
        np.nan_to_num(get_value(row_df, 'sp_t5')))
    prod.skips = int(np.nan_to_num(get_value(row_df, 'skips')))
    prod.save()

    # create/ update time breakdown values
    try:
        time_breakdown = TimeBreakdown.objects.create(daily=day)

    except IntegrityError:
        time_breakdown = TimeBreakdown.objects.get(daily=day)

    time_breakdown.rec_hours = get_value(row_df, 'rec_hours')
    time_breakdown.logistics = get_value(row_df, 'logistics')
    time_breakdown.beyond_control = get_value(row_df, 'beyond_contractor_control')
    time_breakdown.other_downtime = get_value(row_df, 'other_dt')
    time_breakdown.rec_moveup = np.nan
    time_breakdown.camp_move = np.nan
    time_breakdown.wait_source = np.nan
    time_breakdown.wait_layout = np.nan
    time_breakdown.wait_shift_change = np.nan
    time_breakdown.company_suspension = np.nan
    time_breakdown.company_tests = np.nan
    time_breakdown.line_fault = np.nan
    time_breakdown.instrument_fault = np.nan
    time_breakdown.vibrator_fault = np.nan
    time_breakdown.incident = np.nan
    time_breakdown.holiday = np.nan
    time_breakdown.recovering = np.nan
    time_breakdown.save()

    return day.production_date


def main():
    project = Project.objects.get(project_name=project_name)
    for month in months:
        day_df = pd.read_excel(report_filename, sheet_name=month, header=None)

        for row in islice(day_df.iterrows(), 26, None):
            day_date = populate_report(project, row)
            if not day_date:
                break
            print(f'date {day_date.strftime("%d-%b-%Y")} processed')


if __name__ == '__main__':
    main()
