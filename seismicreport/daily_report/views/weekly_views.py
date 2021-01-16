from django.conf import settings
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views.generic import View
from daily_report.models.daily_models import Daily
from daily_report.forms.weekly_forms import WeeklyForm
from daily_report.report_backend import ReportInterface
from daily_report.week_backend import WeeklyInterface
from seismicreport.vars import AVG_PERIOD, SS_2
from seismicreport.utils.plogger import Logger
from seismicreport.utils.get_ip import get_client_ip
from seismicreport.utils.utils_funcs import string_to_date, date_to_string

logger = Logger.getlogger()
#TODO first button to be a dropdown list of last 10 weekly reports


@method_decorator(login_required, name='dispatch')
class WeeklyView(View):

    form_week = WeeklyForm
    template_weekly_page = 'daily_report/weekly_page.html'
    r_iface = ReportInterface(settings.MEDIA_ROOT)
    w_iface = WeeklyInterface(settings.MEDIA_ROOT)

    def get(self, request, daily_id):
        try:
            # get daily report from id
            day = Daily.objects.get(id=daily_id)

        except Daily.DoesNotExist:
            return redirect('daily_page', daily_id)

        week_initial = self.w_iface.get_week_values(day)
        totals_prod, totals_time, totals_hse = self.r_iface.calc_totals(day)
        totals_rcvr = self.r_iface.calc_receiver_totals(day)
        days, weeks = self.w_iface.collate_weekdata(day)

        if day.project.planned_vp > 0:
            proj_complete = (
                (totals_prod['proj_total'] + totals_prod['proj_skips']) /
                day.project.planned_vp
            )

        else:
            proj_complete = 0

        est_complete = self.r_iface.calc_est_completion_date(
            day, AVG_PERIOD, day.project.planned_vp, proj_complete)

        totals_prod['proj_area'] = day.project.planned_area * proj_complete
        totals_prod['proj_complete'] = proj_complete * 100
        totals_prod['est_complete'] = est_complete

        context = {
            'daily_id': daily_id,
            'SS_2': SS_2,
            'totals_production': totals_prod,
            'totals_time': totals_time,
            'totals_hse': totals_hse,
            'totals_receiver': totals_rcvr,
            'days': days,
            'weeks': weeks,
            'form_week': self.form_week(initial=week_initial),
        }

        return render(request, self.template_weekly_page, context)

    def post(self, request, daily_id):
        day = None
        try:
            day = Daily.objects.get(id=daily_id)

        except day.DoesNotExist:
            redirect('daily_page', 0)

        if request.method == 'POST':
            ip_address = get_client_ip(request)
            user = request.user
            button_pressed = request.POST.get('button_pressed', '')

            if button_pressed == 'submit':
                week_form = self.form_week(request.POST)
                if week_form.is_valid():
                    week_comment = week_form.cleaned_data.get('csr_week_comment', '')
                    author = week_form.cleaned_data.get('author', '')
                    self.w_iface.update_week_report(day, week_comment, author)
                    logger.info(
                        f'user {user.username} (ip: {ip_address}) made comment '
                        f'in week report {day.production_date} for '
                        f'{day.project.project_name}:\n{week_comment}'
                    )

            elif button_pressed == 'delete':
                self.w_iface.delete_week_report(day)

        return redirect('weekly_page', daily_id)


# def csr_weekly_excel_report(request, daily_id):

#     rprt_iface = ReportInterface('')

#     try:
#         # get daily report from id
#         day = Daily.objects.get(id=daily_id)
#         project = day.project
#         day, _ = rprt_iface.load_report_db(project, day.production_date)

#     except Daily.DoesNotExist:
#         return redirect('daily_page', 0)

#     report_data = collate_excel_weeklyreport_data(day)
#     csr_report = ExcelReport(report_data, settings.MEDIA_ROOT, settings.STATIC_ROOT)
#     csr_report.create_dailyreport()

#     #TODO save excel: improve file handling, name sheet, set to A4, fit to page print
#     # note FileResponse will close the file/ buffer - do not use with block
#     f_excel = csr_report.save_excel()
#     return FileResponse(f_excel, as_attachment=True, filename='csr_report.xlsx')
