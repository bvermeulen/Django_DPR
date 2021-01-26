import calendar
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views.generic import View
from django.db.utils import IntegrityError
from  daily_report.models.project_models import Project
from daily_report.models.service_models import (
    Service, ServiceTask, TaskQuantity,
)
from daily_report.models.daily_models import Daily
from daily_report.forms.service_forms import MonthDaysForm
from daily_report.report_backend import ReportInterface
from seismicreport.vars import NAME_LENGTH, DESCR_LENGTH, RIGHT_ARROW, LEFT_ARROW
from seismicreport.utils.utils_funcs import date_to_string, string_to_date
from seismicreport.utils.plogger import Logger
from seismicreport.utils.get_ip import get_client_ip
from seismicreport.utils.utils_funcs import toggle_month

logger = Logger.getlogger()


@method_decorator(login_required, name='dispatch')
class ServiceView(View):

    template_services_page = 'daily_report/services_page.html'
    ri = ReportInterface('')

    def get(self, request, project_name):
        services = Service.objects.filter(
            project__project_name=project_name).order_by('service_contract')
        daily_id, report_date = self.ri.get_latest_report_id(project_name)
        try:
            year = report_date.year
            month = report_date.month

        except AttributeError:
            year = None
            month = None

        context = {
            'services': services,
            'project_name': project_name,
            'daily_id': daily_id,
            'year': year,
            'month': month,
        }
        return render(request, self.template_services_page, context)

    def post(self, request, project_name):
        new_service_name = request.POST.get('new_service_name', '')[:NAME_LENGTH]
        new_service_description = request.POST.get('new_service_description', '')[:DESCR_LENGTH]  #pylint: disable=line-too-long
        edit_service = request.POST.get('edit_service', '')[:NAME_LENGTH]
        new_task_name = request.POST.get('new_task_name', '')[:NAME_LENGTH]
        new_task_description = request.POST.get('new_task_description', '')[:DESCR_LENGTH]
        new_task_unit = request.POST.get('new_task_unit', '')[:NAME_LENGTH]
        edit_task = request.POST.get('edit_task', '')[:NAME_LENGTH]
        service_name = request.POST.get('service_name', '')[:NAME_LENGTH]
        delete_service = request.POST.get('delete_service', '')[:NAME_LENGTH]
        delete_task = request.POST.get('delete_task', '')
        if delete_task:
            service_name, delete_task = [v.strip()[:NAME_LENGTH]
                                         for v in delete_task.split(',')]
        project = Project.objects.get(project_name=project_name)
        daily_id, report_date = self.ri.get_latest_report_id(project_name)
        try:
            year = report_date.year
            month = report_date.month

        except AttributeError:
            year = None
            month = None

        self.create_edit_delete_service(
            project, new_service_name, new_service_description,
            edit_service, delete_service,
        )
        self.create_edit_delete_task(
            project, service_name, new_task_name, new_task_description, new_task_unit,
            edit_task, delete_task,
        )
        services = Service.objects.filter(project=project).order_by('service_contract')
        context = {
            'services': services,
            'project_name': project_name,
            'daily_id': daily_id,
            'year': year,
            'month': month,
        }

        logger.info(
            f'user {request.user.username} (ip: {get_client_ip(request)}) '
            f'made changes in services for {project_name}'
        )

        return render(request, self.template_services_page, context)

    @staticmethod
    def create_edit_delete_service(
            project, service_name, service_description, edit_service, delete_service,
        ):

        if not (delete_service or edit_service or service_name):
            return

        # delete service
        if delete_service:
            try:
                service = Service.objects.get(
                    project=project, service_contract=delete_service)
                service.delete()
                return

            except Service.DoesNotExist:
                return

         # edit an existing service
        if edit_service and service_name:
            try:
                service = Service.objects.get(
                    project=project, service_contract=edit_service)
                service.service_contract = service_name
                service.description = service_description
                service.save()
                return

            except (Service.DoesNotExist, IntegrityError):
                return

        # create a new service
        if not edit_service and service_name:
            try:
                Service.objects.create(
                    project=project,
                    service_contract=service_name,
                    description=service_description,
                )

            except IntegrityError:
                pass

        return

    @staticmethod
    def create_edit_delete_task(
            project, service_name, task_name, task_description, task_unit,
            edit_task, delete_task,
        ):

        if not (delete_task or edit_task or task_name):
            return

        try:
            service = Service.objects.get(
                project=project,
                service_contract=service_name,
            )

        except Service.DoesNotExist:
            return

        # delete task
        if delete_task:
            try:
                task = ServiceTask.objects.get(
                    service=service, task_name=delete_task)
                task.delete()
                return

            except ServiceTask.DoesNotExist:
                return

        # edit an existing task
        if edit_task and task_name:
            try:
                task = ServiceTask.objects.get(
                    service=service, task_name=edit_task)
                task.task_name = task_name
                task.task_description = task_description
                task.task_unit = task_unit
                task.save()
                return

            except (ServiceTask.DoesNotExist, IntegrityError):
                return

        # create a new task
        if not edit_task:
            try:
                ServiceTask.objects.create(
                    service=service,
                    task_name=task_name,
                    task_description=task_description,
                    task_unit=task_unit,
                )

            except IntegrityError:
                pass

        return


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
