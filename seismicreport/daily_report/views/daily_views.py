from datetime import timedelta
import calendar
from django.conf import settings
from django.http import FileResponse
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.utils.datastructures import MultiValueDictKeyError
from django.contrib.auth.decorators import login_required
from django.views.generic import View
from daily_report.models.daily_models import Daily
from daily_report.models.project_models import TaskQuantity
from daily_report.forms.project_forms import ProjectControlForm
from daily_report.forms.daily_forms import DailyForm, MonthDaysForm
from daily_report.report_backend import ReportInterface
from daily_report.excel_backend import ExcelReport
from seismicreport.vars import RIGHT_ARROW, LEFT_ARROW, AVG_PERIOD, NO_DATE_STR
from seismicreport.utils.plogger import Logger
from seismicreport.utils.get_ip import get_client_ip
from seismicreport.utils.utils_funcs import toggle_month, string_to_date, date_to_string

logger = Logger.getlogger()


@method_decorator(login_required, name='dispatch')
class DailyView(View):

    form_daily = DailyForm
    form_project_control = ProjectControlForm
    template_daily_page = 'daily_report/daily_page.html'
    ri = ReportInterface(settings.MEDIA_ROOT)
    arrow_symbols = {'right': RIGHT_ARROW, 'left': LEFT_ARROW}

    def get(self, request, daily_id):
        report_date_str = ''
        project_name = ''

        try:
            # get daily report from id
            day = Daily.objects.get(id=daily_id)
            day, day_initial = self.ri.load_report_db(day.project, day.production_date)

        except Daily.DoesNotExist:
            # get daily report from session project_name and report_date
            project_name = request.session.get('selected_project', '')
            project = self.ri.get_project(project_name)
            report_date = string_to_date(request.session.get('report_date', ''))
            day, day_initial = self.ri.load_report_db(project, report_date)

        if day:
            form_project_control = self.form_project_control(initial={
                'projects': day.project.project_name,
                'report_date':day.production_date.strftime('%#d %b %Y'),
            })
            totals_production, totals_time, totals_hse = self.ri.calc_totals(day)
            context = {
                'form_daily': self.form_daily(initial=day_initial),
                'totals_production': totals_production,
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

            context = {'arrow_symbols': self.arrow_symbols,
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

            project = self.ri.get_project(project_name)

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
                # Get the report_file from request and store it as a standard report
                # file in media. Close the report_file to delete it.
                # Keep the file name is session for later use.
                report_file = request.FILES['daily_report_file']
                report_date = self.ri.save_report_file(project, report_file)
                logger.info(
                    f'user {user.username} (ip: {ip_address}) '
                    f'uploaded {report_file} for {report_date} for {project.project_name}'
                )

            except MultiValueDictKeyError:
                pass

            day, _ = self.ri.load_report_db(project, report_date)
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
                        f'in report {day.production_date} for '
                        f'{day.project.project_name}:\n'
                        f'{csr_comment}'
                    )

            request.session['selected_project'] = project_name
            request.session['report_date'] = date_to_string(report_date)

        day_id = day.id if day else 0
        return redirect('daily_page', day_id)


@method_decorator(login_required, name='dispatch')
class MonthlyServiceView(View):

    form_days = MonthDaysForm
    template_monthly_services = 'daily_report/monthly_services.html'
    arrow_symbols = {'right': RIGHT_ARROW, 'left': LEFT_ARROW}

    def get(self, request, daily_id, year, month):
        try:
            day = Daily.objects.get(id=daily_id)
            project = day.project
            request.session['report_date'] = date_to_string(day.production_date)

        except Daily.DoesNotExist:
            return redirect('daily_page', daily_id)

        dayrange = range(1, calendar.monthrange(year, month)[1] + 1)
        _my = string_to_date('-'.join([str(year), str(month), '1']))
        services = {
            'project': project.project_name,
            'year': _my.strftime('%Y'),
            'month':_my.strftime('%B')
        }
        for service in project.services.all().order_by('service_contract'):
            services[service.id] = {}
            services[service.id]['name'] = service.description
            services[service.id]['tasks'] = {}
            for task in service.tasks.all().order_by('task_name'):
                services[service.id]['tasks'][task.id] = {}
                services[service.id]['tasks'][task.id]['name'] = task.task_name

                day_qties = task.get_monthly_task_quantities(year, month)
                initial = {f'{year}-{month:02}-{day:02}': 0 for day in dayrange}
                total = 0
                for dq in day_qties:
                    total += dq.quantity
                    initial[f'{year}-{month:02}-{dq.date.day:02}'] = dq.quantity

                services[service.id]['tasks'][task.id]['form_task'] = (
                    self.form_days(year, month, initial=initial, prefix=task.id)
                )
                services[service.id]['tasks'][task.id]['total'] = total

        context = {
            'daily_id': daily_id,
            'services': services,
            'arrow_symbols': self.arrow_symbols,
        }
        return render(request, self.template_monthly_services, context)

    def post(self, request, daily_id, year, month):
        try:
            day = Daily.objects.get(id=daily_id)
            project = day.project
            request.session['report_date'] = date_to_string(day.production_date)

        except Daily.DoesNotExist:
            return redirect('daily_page', daily_id)

        left = self.arrow_symbols['left']
        right = self.arrow_symbols['right']

        logger.info(
            f'user {request.user.username} (ip: {get_client_ip(request)}) is '
            f'updating services {project.project_name} for {year}-{month}'
        )

        if request.method == 'POST':
            button_pressed = request.POST.get('button_pressed')

            if button_pressed in [left, right]:
                if button_pressed == left:
                    year, month = toggle_month(year, month, -1)

                if button_pressed == right:
                    year, month = toggle_month(year, month, +1)

                redirect('monthly_service_page', daily_id, year, month)

            for task in [task for srv in project.services.all()
                         for task in srv.tasks.all()]:
                form_tsk_qts = self.form_days(year, month, request.POST, prefix=task.id)

                if form_tsk_qts.is_valid():
                    tsk_qts = form_tsk_qts.cleaned_data
                    self.update_task_quantity(task, tsk_qts)

                else:
                    continue

        return redirect('monthly_service_page', daily_id, year, month)

    @staticmethod
    def update_task_quantity(task, task_qts: dict) -> None:
        for task_date, qty in task_qts.items():
            # check quantity (float) and date ('YYYY-MM-DD')
            if qty is None or not isinstance(qty, float) or task_date is None:
                continue

            if not string_to_date(task_date):
                continue

            # create/ update TaskQuantity object
            try:
                tq = TaskQuantity.objects.get(
                    task=task,
                    date=task_date,
                )

                if abs(float(qty)) < 0.01:
                    tq.delete()

                else:
                    tq.quantity = float(qty)
                    tq.save()

            except TaskQuantity.DoesNotExist:
                if abs(float(qty)) < 0.01:
                    continue

                else:
                    tq = TaskQuantity.objects.create(
                        task=task,
                        date=task_date,
                        quantity=float(qty)
                    )


def csr_excel_report(request, daily_id):
    ri = ReportInterface(settings.MEDIA_ROOT)
    try:
        # get daily report from id
        day = Daily.objects.get(id=daily_id)
        project = day.project
        day, _ = ri.load_report_db(project, day.production_date)

    except Daily.DoesNotExist:
        return redirect('daily_page', 0)

    totals_production, totals_time, totals_hse = ri.calc_totals(day)
    project = day.project

    report_data = {}
    report_data['report_date'] = day.production_date.strftime('%#d %b %Y')

    if project.planned_start_date:
        proj_start_str = project.planned_start_date.strftime('%#d %b %Y')
        ops_days = (day.production_date - project.planned_start_date).days

    else:
        proj_start_str = NO_DATE_STR
        ops_days = NO_DATE_STR

    report_data['project_table'] = {
        'Project': project.project_name,
        'Project VPs': project.planned_vp,
        'Area (km\u00B2)': project.planned_area,
        'Proj. Start': proj_start_str,
        'Crew': project.crew_name,
    }

    report_data['daily_table'] = {
        'Oper Day': ops_days,
        'Total VPs': totals_production['total_sp'],
        'Target VPs': totals_production['ctm'][0],
        '% Target': totals_production['ctm'][1],
        'Recording Hrs': totals_time['rec_time'],
        'Standby Hrs': totals_time['standby'],
        'Downtime Hrs': totals_time['downtime'],
        'Skip VPs': totals_production['skips'],
    }

    report_data['csr_table'] = {
        f'{p.department}_{i:02}': p.name for i, p in enumerate(day.staff.all())
    }

    # proj_stats
    proj_total = totals_production['proj_total']
    proj_skips = totals_production['proj_skips']
    if project.planned_vp > 0:
        proj_complete = (proj_total + proj_skips) / project.planned_vp

    else:
        proj_complete = 0


    report_data['proj_stats_table'] = {
        'Recorded VPs': proj_total,
        'Area (km\u00B2)': project.planned_area * proj_complete,
        'Skip VPs': proj_skips,
        '% Complete': proj_complete,
        'Est. Complete': ri.calc_est_completion_date(
            day, AVG_PERIOD, project.planned_vp, proj_complete),
    }

    # block_stats
    block = day.block
    totals_block = ri.calc_block_totals(day)
    if block and totals_block:
        block_name = block.block_name
        block_total = totals_block['block_total'] + totals_block['block_skips']
        block_complete = block_total / block.block_planned_vp
        block_area = block.block_planned_area * block_complete
        block_completion_date = ri.calc_est_completion_date(
            day, AVG_PERIOD, block.block_planned_vp, block_complete)

    else:
        block_name = ''
        block_complete = 0
        block_area = 0
        block_total = 0
        block_completion_date = NO_DATE_STR

    report_data['block_stats_table'] = {
        'Block': block_name,
        'Area (km\u00B2)': block_area,
        '% Complete': block_complete,
        'Est. Complete': block_completion_date,
    }

    report_data['hse_stats_table'] = {
        'LTI': totals_hse['lti'],
        'RWC': totals_hse['rwc'],
        'MTC': totals_hse['mtc'],
        'FAC': totals_hse['fac'],
        'NM/ Incidents': totals_hse['incident_nm'],
        'LSR': totals_hse['lsr_violations'],
        'STOP': totals_hse['stop'],
    }

    report_data['csr_comment_table'] = {
        'Comments': day.csr_comment,
    }

    csr_report = ExcelReport(report_data)
    csr_report.create_dailyreport()

    #TODO save excel: improve file handling, name sheet, set to A4, fit to page print
    # note FileResponse will close the file/ buffer - do not use with block
    f_excel = csr_report.save_excel(settings.MEDIA_ROOT)
    return FileResponse(f_excel, as_attachment=True, filename='csr_report.xlsx')
