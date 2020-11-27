''' utility function that can be used throughout the app
'''
from datetime import datetime
import numpy as np


def nan_array(a_list: list):
    ''' convert list to np.array, converting nan values to zero
    '''
    np_array = np.array(a_list)
    nan_where = np.isnan(np_array)
    np_array[nan_where] = 0
    return np_array


def calc_ratio(a, b):
    ''' calculates ratio a/b, gives np.nan when b is zero
    '''
    if not np.isnan(b) and b > 0:
        return a / b

    else:
        return np.nan


def toggle_month(year: int, month: int, deltamonths: int) -> tuple:
    ''' returns year and month based on change of number of months
        arguments:
            year: current year (integer)
            month: current month (integer)
            deltamonths: difference in months (integer)
    '''
    new_month = month + deltamonths
    year += (new_month -1) // 12
    month = (new_month - 1) % 12 + 1
    return year, month


def date_to_string(date_object: datetime) -> str:
    '''  converts a date object to a string with 'YYYY-MM-DD'
         returns an empty string if no conversion is possible
         or date_object is empty or None
    '''
    if not date_object:
        return ''

    try:
        return date_object.strftime('%Y-%m-%d')

    except AttributeError:
        return ''


def string_to_date(date_str: str) -> datetime:
    ''' converts a string object with format 'YYYY-MM-DD to a date object
        returns an datetime(1900, 1, 1) is no conversion is possible
    '''
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')

    except ValueError:
        return  datetime(1900, 1, 1)
