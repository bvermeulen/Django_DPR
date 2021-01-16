from datetime import timedelta
import warnings
import numpy as np
from django.db.models import Q
from daily_report.models.daily_models import HseWeather
from seismicreport.vars import WEEKDAYS, hse_weather_schema
from seismicreport.utils.utils_funcs import nan_array


#pylint: disable=no-value-for-parameter
warnings.filterwarnings('ignore')


class Mixin:

    @staticmethod
    def day_hse_totals(daily):
        try:
            hse = HseWeather.objects.get(daily=daily)

        except HseWeather.DoesNotExist:
            d_hse = {f'{key}': '' for key in hse_weather_schema}
            d_hse['toolbox_text'] = ''
            d_hse['weather_text'] = ''
            return d_hse

        # HSE stats
        d_hse = {f'{key}': np.nan_to_num(getattr(hse, key))
                 for key in hse_weather_schema}

        # toolboxes
        d_hse['toolbox_text'] = ''
        for tb in hse.toolboxes.all():
            d_hse['toolbox_text'] += f'- {tb.toolbox}\n'

        # weather
        d_hse['weather_text'] = (
            f'Weather condition: {d_hse["weather_condition"]}, rain: {d_hse["rain"]}\n'
            f'Temperatures: minimum {d_hse["temp_min"]:.1f}, maxumum {d_hse["temp_max"]:.1f}\n'  #pylint: disable=line-too-long
        )

        return d_hse

    @staticmethod
    def week_hse_totals(daily):
        end_date = daily.production_date
        start_date = end_date - timedelta(days=WEEKDAYS)

        hse_query = HseWeather.objects.filter(
            Q(daily__production_date__gte=start_date),
            Q(daily__production_date__lte=end_date),
            daily__project=daily.project,
        )

        if not hse_query:
            return {f'week_{key}': '' for key in hse_weather_schema}

        w_hse = {f'week_{key}': sum(nan_array([val[key] for val in hse_query.values()]))
                 for key in hse_weather_schema[:12]}

        return w_hse

    @staticmethod
    def month_hse_totals(daily):

        hse_query = HseWeather.objects.filter(
            Q(daily__production_date__year=daily.production_date.year) &
            Q(daily__production_date__month=daily.production_date.month) &
            Q(daily__production_date__day__lte=daily.production_date.day),
            daily__project=daily.project,
        )

        if not hse_query:
            return {f'month_{key}': '' for key in hse_weather_schema}

        m_hse = {f'month_{key}': sum(nan_array([val[key] for val in hse_query.values()]))
                 for key in hse_weather_schema[:12]}

        return m_hse

    @staticmethod
    def proj_hse_totals(daily):
        hse_query = HseWeather.objects.filter(
            daily__production_date__lte=daily.production_date,
            daily__project=daily.project,
        ).order_by('daily__production_date')

        if not hse_query:
            return {f'proj_{key}': '' for key in hse_weather_schema}

        p_hse = {f'proj_{key}': sum(nan_array([val[key] for val in hse_query.values()]))
                 for key in hse_weather_schema[:12]}

        return p_hse
