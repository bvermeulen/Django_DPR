import numpy as np
from django.db.models import Q
from daily_report.models.project_models import ReceiverType
from daily_report.models.daily_models import ReceiverProduction
from seismicreport.vars import RECEIVERTYPE_NAME, receiver_prod_schema
from seismicreport.utils.plogger import Logger
from seismicreport.utils.utils_funcs import nan_array

logger = Logger.getlogger()

class ReceiverInterface:

    @staticmethod
    def day_receiver_total(daily, receivertype):

        try:
            rcvr = ReceiverProduction.objects.get(daily=daily, receivertype=receivertype)

        except ReceiverProduction.DoesNotExist:
            d_rcvr = {f'{key}': 0 for key in receiver_prod_schema}
            return d_rcvr

        d_rcvr = {f'{key}': np.nan_to_num(getattr(rcvr, key))
                  for key in receiver_prod_schema}

        return d_rcvr

    @staticmethod
    def month_receiver_total(daily, receivertype):
        rcvr_query = ReceiverProduction.objects.filter(
            Q(daily__production_date__year=daily.production_date.year) &
            Q(daily__production_date__month=daily.production_date.month) &
            Q(daily__production_date__day__lte=daily.production_date.day),
            receivertype=receivertype,
        )

        if not rcvr_query:
            return {}

        m_rcvr = {
            f'month_{key}': sum(nan_array([val[key] for val in rcvr_query.values()]))
            for key in receiver_prod_schema
        }

        return m_rcvr

    @staticmethod
    def project_receiver_total(daily, receivertype):
        rcvr_query = ReceiverProduction.objects.filter(
            daily__production_date__lte=daily.production_date,
            receivertype=receivertype,
        )

        if not rcvr_query:
            return {}

        p_rcvr = {
            f'proj_{key}': sum(nan_array([val[key] for val in rcvr_query.values()]))
            for key in receiver_prod_schema
        }

        return p_rcvr

    def calc_receiver_totals(self, daily):
        ''' method to calc the receiver totals. Outstanding:
            loop over receivertypes and handling of qc_field, qc_camp, upload
        '''
        try:
            rt = ReceiverType.objects.get(
                project=daily.project, receivertype_name=RECEIVERTYPE_NAME)

        except ReceiverType.DoesNotExist:
            return {}

        d_rcvr = self.day_receiver_total(daily, rt)
        m_rcvr = self.month_receiver_total(daily, rt)
        p_rcvr = self.project_receiver_total(daily, rt)

        return {**d_rcvr, **m_rcvr, **p_rcvr}
