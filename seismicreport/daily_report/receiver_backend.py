from datetime import timedelta
import numpy as np
from django.db.models import Q
from daily_report.models.daily_models import ReceiverProduction
from seismicreport.vars import RECEIVERTYPE_NAME, WEEKDAYS, receiver_prod_schema
from seismicreport.utils.plogger import Logger, timed
from seismicreport.utils.utils_funcs import nan_array

logger = Logger.getlogger()

class Mixin:

    @staticmethod
    def day_receiver_total(daily, receivertype_name):

        try:
            rcvr = ReceiverProduction.objects.get(
                daily=daily,
                receivertype=daily.project.receivertypes.get(
                    receivertype_name=receivertype_name),
                )

        except ReceiverProduction.DoesNotExist:
            d_rcvr = {f'{key}': 0 for key in receiver_prod_schema}
            return d_rcvr

        d_rcvr = {f'{key}': np.nan_to_num(getattr(rcvr, key))
                  for key in receiver_prod_schema}

        return d_rcvr

    @staticmethod
    def week_receiver_total(daily, receivertype_name):
        end_date = daily.production_date
        start_date = end_date - timedelta(days=WEEKDAYS-1)
        rcvr_query = ReceiverProduction.objects.filter(
            Q(daily__production_date__gte=start_date),
            Q(daily__production_date__lte=end_date),
            receivertype = daily.project.receivertypes.get(
                receivertype_name=receivertype_name
            ),
        )

        if not rcvr_query:
            w_rcvr = {f'week_{key}': 0 for key in receiver_prod_schema}
            return w_rcvr

        w_rcvr = {
            f'week_{key}': sum(nan_array([val[key] for val in rcvr_query.values()]))
            for key in receiver_prod_schema
        }

        return w_rcvr

    @staticmethod
    def month_receiver_total(daily, receivertype_name):
        rcvr_query = ReceiverProduction.objects.filter(
            Q(daily__production_date__year=daily.production_date.year) &
            Q(daily__production_date__month=daily.production_date.month) &
            Q(daily__production_date__day__lte=daily.production_date.day),
            receivertype = daily.project.receivertypes.get(
                receivertype_name=receivertype_name
            ),
        )

        if not rcvr_query:
            m_rcvr = {f'month_{key}': 0 for key in receiver_prod_schema}
            return m_rcvr

        m_rcvr = {
            f'month_{key}': sum(nan_array([val[key] for val in rcvr_query.values()]))
            for key in receiver_prod_schema
        }

        return m_rcvr

    @staticmethod
    def project_receiver_total(daily, receivertype_name):
        rcvr_query = ReceiverProduction.objects.filter(
            daily__production_date__lte=daily.production_date,
            receivertype = daily.project.receivertypes.get(
                receivertype_name=receivertype_name
            ),
        )

        if not rcvr_query:
            p_rcvr = {f'proj_{key}': 0 for key in receiver_prod_schema}
            return p_rcvr

        p_rcvr = {
            f'proj_{key}': sum(nan_array([val[key] for val in rcvr_query.values()]))
            for key in receiver_prod_schema
        }

        return p_rcvr

    @timed(logger, print_log=True)
    def calc_receiver_totals(self, daily):
        ''' method to calc the receiver totals. Outstanding:
            loop over receivertypes and handling of qc_field, qc_camp, upload
        '''
        d_rcvr = self.day_receiver_total(daily, RECEIVERTYPE_NAME)
        w_rcvr = self.week_receiver_total(daily, RECEIVERTYPE_NAME)
        m_rcvr = self.month_receiver_total(daily, RECEIVERTYPE_NAME)
        p_rcvr = self.project_receiver_total(daily, RECEIVERTYPE_NAME)

        return {**d_rcvr, **w_rcvr, **m_rcvr, **p_rcvr}
