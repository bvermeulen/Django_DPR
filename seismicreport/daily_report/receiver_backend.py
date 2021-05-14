from datetime import timedelta
import numpy as np
from django.db.models import Q
from daily_report.models.daily_models import ReceiverProduction
from seismicreport.vars import WEEKDAYS, receiver_prod_schema
from seismicreport.utils.plogger import Logger
from seismicreport.utils.utils_funcs import nan_array, nan_avg_array

logger = Logger.getlogger()

class Mixin:

    @staticmethod
    def day_receiver_total(daily, receivertype):
        if daily:
            try:
                rcvr = ReceiverProduction.objects.get(
                    daily=daily,
                    receivertype=receivertype,
                )

            except ReceiverProduction.DoesNotExist:
                d_rcvr = {f'day_{key}': 0 for key in receiver_prod_schema}
                return d_rcvr

        else:
            d_rcvr = {f'day_{key}': 0 for key in receiver_prod_schema}
            return d_rcvr

        d_rcvr = {f'day_{key}': np.nan_to_num(getattr(rcvr, key))
                  for key in receiver_prod_schema}

        return d_rcvr

    @staticmethod
    def week_receiver_total(daily, receivertype):
        if daily:
            end_date = daily.production_date
            start_date = end_date - timedelta(days=WEEKDAYS-1)
            rcvr_query = ReceiverProduction.objects.filter(
                Q(daily__production_date__gte=start_date),
                Q(daily__production_date__lte=end_date),
                receivertype = receivertype,
            )
        else:
            rcvr_query = None

        if not rcvr_query:
            w_rcvr = {f'week_{key}': 0 for key in receiver_prod_schema}
            return w_rcvr

        w_rcvr = {
            f'week_{key}': sum(nan_array([val[key] for val in rcvr_query.values()]))
            for key in receiver_prod_schema if key != 'qc_field'
        }
        w_rcvr['week_qc_field'] = nan_avg_array([val['qc_field'] for val in rcvr_query.values()])

        return w_rcvr

    @staticmethod
    def month_receiver_total(daily, receivertype):
        if daily:
            rcvr_query = ReceiverProduction.objects.filter(
                Q(daily__production_date__year=daily.production_date.year) &
                Q(daily__production_date__month=daily.production_date.month) &
                Q(daily__production_date__day__lte=daily.production_date.day),
                receivertype = receivertype,
            )

        else:
            rcvr_query = None

        if not rcvr_query:
            m_rcvr = {f'month_{key}': 0 for key in receiver_prod_schema}
            return m_rcvr

        m_rcvr = {
            f'month_{key}': sum(nan_array([val[key] for val in rcvr_query.values()]))
            for key in receiver_prod_schema if key != 'qc_field'
        }
        m_rcvr['month_qc_field'] = nan_avg_array([val['qc_field'] for val in rcvr_query.values()])

        return m_rcvr

    @staticmethod
    def project_receiver_total(daily, receivertype):
        if daily:
            rcvr_query = ReceiverProduction.objects.filter(
                daily__production_date__lte=daily.production_date,
                receivertype = receivertype,
            ).order_by('daily__production_date')

        else:
            rcvr_query = None

        if not rcvr_query:
            p_rcvr = {f'proj_{key}': 0 for key in receiver_prod_schema}
            return p_rcvr, {}

        rcvr_series = {
            f'{key}_series': [val[key] for val in rcvr_query.values()]
            for key in receiver_prod_schema
        }
        p_rcvr = {
            f'proj_{key}': sum(nan_array([val[key] for val in rcvr_query.values()]))
            for key in receiver_prod_schema if key != 'qc_field'
        }

        p_rcvr['proj_qc_field'] = nan_avg_array([val['qc_field'] for val in rcvr_query.values()])

        return p_rcvr, rcvr_series
