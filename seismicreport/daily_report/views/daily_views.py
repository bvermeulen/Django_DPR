from datetime import timedelta
from django.conf import settings
from django.http import FileResponse
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.utils.datastructures import MultiValueDictKeyError
from django.contrib.auth.decorators import login_required
from django.views.generic import View
from daily_report.models.daily_models import Daily
from daily_report.forms.project_forms import ProjectControlForm
from daily_report.forms.daily_forms import DailyForm
from daily_report.report_backend import ReportInterface
from daily_report.excel_daily_backend import (
    ExcelDayReport, collate_excel_dailyreport_data
)
from seismicreport.vars import RIGHT_ARROW, LEFT_ARROW
from seismicreport.utils.plogger import Logger
from seismicreport.utils.get_ip import get_client_ip
from seismicreport.utils.utils_funcs import string_to_date, date_to_string

logger = Logger.getlogger()


@method_decorator(login_required, name='dispatch')
class DailyView(View):

    form_daily = DailyForm
    form_project_control = ProjectControlForm
    template_daily_page = 'daily_report/daily_page.html'
    rprt_iface = ReportInterface(settings.MEDIA_ROOT)
    arrow_symbols = {'right': RIGHT_ARROW, 'left': LEFT_ARROW}

    def get(self, request, daily_id):
        report_date_str = ''
        project_name = ''

        try:
            # get daily report from id
            day = Daily.objects.get(id=daily_id)
            day, day_initial = self.rprt_iface.load_report_db(
                day.project, day.production_date)

        except Daily.DoesNotExist:
            # get daily report from session project_name and report_date
            project_name = request.session.get('selected_project', '')
            project = self.rprt_iface.get_project(project_name)
            report_date = string_to_date(request.session.get('report_date', ''))
            day, day_initial = self.rprt_iface.load_report_db(project, report_date)

        if day:
            form_project_control = self.form_project_control(initial={
                'projects': day.project.project_name,
                'report_date':day.production_date.strftime('%#d %b %Y'),
            })
            (
                _,
                totals_production,
                totals_time,
                totals_receiver,
                totals_hse
             ) = self.rprt_iface.calc_totals(day)

            self.rprt_iface.create_daily_graphs()
            context = {
                'form_daily': self.form_daily(initial=day_initial),
                'totals_production': totals_production,
                'totals_receiver': totals_receiver,
                'totals_time': totals_time,
                'totals_hse': totals_hse,
                'arrow_symbols': self.arrow_symbols,
                'form_project_control': form_project_control,
            }

        else:
            # if there is a date format for display in template
            if report_date:
                report_date_str = report_date.strftime('%#d %b %Y')

            form_project_control = self.form_project_control(initial={
                'projects': project_name,
                'report_date': report_date_str,
            })

            context = {
                'arrow_symbols': self.arrow_symbols,
                'form_project_control': form_project_control,
            }

        return render(request, self.template_daily_page, context)

    def post(self, request, daily_id):
        day = None
        if request.method == 'POST':
            ip_address = get_client_ip(request)
            user = request.user
            form_project_control = self.form_project_control(request.POST)

            if form_project_control.is_valid():
                new_project_name = form_project_control.cleaned_data.get('projects', '')
                if new_project_name:
                    project_name = new_project_name
                else:
                    project_name = request.session.get('selected_project', '')

            project = self.rprt_iface.get_project(project_name)

            button_pressed = request.POST.get('button_pressed', '')
            new_report_date = request.POST.get('report_date', '')
            if new_report_date:
                report_date = new_report_date

            else:
                report_date = request.session.get('report_date', '')

            report_date = string_to_date(report_date)

            if button_pressed == self.arrow_symbols['right']:
                report_date += timedelta(days=1)

            elif button_pressed == self.arrow_symbols['left']:
                report_date -= timedelta(days=1)

            csr_comment = ''
            staff_selected = []
            if button_pressed == 'submit':
                daily_form = self.form_daily(request.POST)
                if daily_form.is_valid():
                    csr_comment = daily_form.cleaned_data.get('csr_comment', '')
                    staff_selected = daily_form.cleaned_data.get('staff')

            try:
                # Get the report_file from request and store it in the database
                report_file = request.FILES['daily_report_file']
                report_date = self.rprt_iface.save_report_file(project, report_file)
                if report_date:
                    logger.info(
                        f'user {user.username} (ip: {ip_address}) '
                        f'uploaded {report_file} for {report_date} '
                        f'for {project.project_name}'
                    )

            except MultiValueDictKeyError:
                pass

            day, _ = self.rprt_iface.load_report_db(project, report_date)
            if day and button_pressed == 'delete':
                logger.info(
                    f'user {user.username} (ip: {ip_address}) '
                    f'deleted report {day.production_date} for {day.project.project_name}'
                )
                day.delete()
                day = None
                report_date = string_to_date('1900-01-01')

            else:
                if day and button_pressed == "submit":
                    day.csr_comment = csr_comment
                    day.staff.set(staff_selected)
                    day.save()
                    logger.info(
                        f'user {user.username} (ip: {ip_address}) made comment '
                        f'in report {day.production_date} '
                        f'for {day.project.project_name}'
                    )

            request.session['selected_project'] = project_name
            request.session['report_date'] = date_to_string(report_date)

        day_id = day.id if day else 0
        return redirect('daily_page', day_id)


@method_decorator(login_required, name='dispatch')
class SourcetypeView(View):

    form_daily = DailyForm
    form_project_control = ProjectControlForm
    template_sourcetype_page = 'daily_report/sourcetype_page.html'
    rprt_iface = ReportInterface(settings.MEDIA_ROOT)
    arrow_symbols = {'right': RIGHT_ARROW, 'left': LEFT_ARROW}

    def get(self, request, daily_id):
        day = None
        try:
            day = Daily.objects.get(id=daily_id)
            day, day_initial = self.rprt_iface.load_report_db(
                day.project, day.production_date
            )

        except Daily.DoesNotExist:
            pass

        if day:
            form_project_control = self.form_project_control(initial={
                'projects': day.project.project_name,
                'report_date':day.production_date.strftime('%#d %b %Y'),
            })
            (
                totals_production_by_type,
                totals_production,
                _,
                _,
                _,
             ) = self.rprt_iface.calc_totals(day)

            context = {
                'daily_id': daily_id,
                'form_daily': self.form_daily(initial=day_initial),
                'form_project_control': form_project_control,
                'totals_production_by_type': totals_production_by_type,
                'totals_production': totals_production,
                'arrow_symbols': self.arrow_symbols,
            }

        else:
            project_name = request.session.get('selected_project', '')
            report_date = string_to_date(request.session.get('report_date', ''))
            if report_date:
                report_date_str = report_date.strftime('%#d %b %Y')
            else:
                report_date_str = ''

            form_project_control = self.form_project_control(initial={
                'projects': project_name,
                'report_date': report_date_str,
            })
            context = {
                'daily_id': daily_id,
                'form_project_control': form_project_control,
                'arrow_symbols': self.arrow_symbols,
            }

        return render(request, self.template_sourcetype_page, context)

    def post(self, request, daily_id):
        day = None
        if request.method == 'POST':
            report_date = request.session.get('report_date', '')
            project_name = request.session.get('selected_project', '')
            project = self.rprt_iface.get_project(project_name)

            button_pressed = request.POST.get('button_pressed', '')

            new_report_date = request.POST.get('report_date', '')
            if new_report_date:
                report_date = new_report_date

            report_date = string_to_date(report_date)

            if button_pressed == self.arrow_symbols['right']:
                report_date += timedelta(days=1)

            elif button_pressed == self.arrow_symbols['left']:
                report_date -= timedelta(days=1)

            request.session['report_date'] = date_to_string(report_date)

            day, _ = self.rprt_iface.load_report_db(project, report_date)

        day_id = day.id if day else 0
        return redirect('sourcetype_page', day_id)


def csr_excel_report(request, daily_id):

    r_iface = ReportInterface('')

    try:
        # get daily report from id
        day = Daily.objects.get(id=daily_id)
        project = day.project
        day, _ = r_iface.load_report_db(project, day.production_date)

    except Daily.DoesNotExist:
        return redirect('daily_page', 0)

    report_data = collate_excel_dailyreport_data(day)
    csr_report = ExcelDayReport(report_data, settings.MEDIA_ROOT, settings.STATIC_ROOT)

    #TODO save excel: improve file handling, name sheet, set to A4, fit to page print
    # note FileResponse will close the file/ buffer - do not use with block
    f_excel = csr_report.create_dailyreport()

    return FileResponse(f_excel, as_attachment=True, filename='csr_report.xlsx')
