''' utility function that can be used throughout the app
'''
import os
from datetime import datetime
import numpy as np
from seismicreport.utils.plogger import Logger

def nan_array(a_list: list):
    ''' convert list to np.array, converting nan values to zero
    '''
    np_array = np.array(a_list)
    nan_where = np.isnan(np_array)
    np_array[nan_where] = 0
    return np_array

def nan_avg_array(a_list: list):
    ''' calculates average of list, ignoring NaN values
    '''
    counter = 0
    sum = 0.0
    for val in a_list:
        if val:
            sum += val
            counter += 1

    if counter > 0:
        return sum / counter

    else:
        return np.nan


def calc_ratio(a, b):
    ''' calculates ratio a/b, gives np.nan when b is zero
    '''
    if np.isnan(a) or np.isnan(b) or b == 0:
        return np.nan

    else:
        return a / b

def calc_avg(a, b):
    if np.isnan(a) or np.isnan(b) or b == 0:
        return np.nan

    else:
        return int(a/ b)


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

def check_expiry_date(expiry_date: datetime):
    logger = Logger.getlogger()
    if datetime.now() > expiry_date:
        warning_str = (
            'License expired: please contact admin@howdiweb.nl to renew the license'
        )
        print(warning_str)
        logger.warning(warning_str)
        os.remove('.env')
        exit()
    else:
        logger.info('License is valid')


def sum_keys(dict_a: dict, dict_b: dict) -> dict:
    ''' function to sum values that have the same key for scalar
        list and tuple. Values must be numerical or np.nan
    '''
    for key, val_b in dict_b.items():
        val_a = dict_a.get(key, None)

        if val_a is not None:
            if isinstance(val_b, (list, tuple)):
                sum_result = []
                for v in zip(val_a, val_b):
                    try:
                        sum_result.append(np.nansum(v))

                    except TypeError:
                        sum_result = val_a

                if isinstance(val_b, tuple):
                    sum_result = tuple(sum_result)

            elif isinstance(val_b, np.ndarray):
                try:
                    where_nan = np.isnan(val_a)
                    val_a[where_nan] = 0
                    where_nan = np.isnan(val_b)
                    val_b[where_nan] = 0
                    sum_result = val_a + val_b

                except TypeError:
                    sum_result = val_a

            else:
                try:
                    sum_result = val_a + val_b

                except TypeError:
                    sum_result = val_a

            dict_a[key] = sum_result

        else:
            dict_a[key] = dict_b[key]

    return dict_a


def get_receivertype_name(project):
    ''' hardwired patch to get receivertype
    '''
    if not project:
        return None

    else:
        try:
            return project.receivertypes.all()[0].receivertype_name

        except IndexError:
            return None
