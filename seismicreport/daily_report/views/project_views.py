import io
from django.shortcuts import render
from django.http import FileResponse
from django.utils.decorators import method_decorator
from django.utils.datastructures import MultiValueDictKeyError
from django.contrib.auth.decorators import login_required
from django.views.generic import View
from django.db.utils import IntegrityError
from seismicreport.utils.utils_funcs import date_to_string
from seismicreport.utils.plogger import Logger
from seismicreport.vars import NAME_LENGTH, DESCR_LENGTH
from daily_report.forms.project_forms import (
    ProjectControlForm, BlockControlForm, SourceTypeControlForm,
    ProjectForm, BlockForm, SourceTypeForm
)
from daily_report.models.project_models import (
    Project, Block, SourceType, Service, ServiceTask,
)
from daily_report.report_backend import ReportInterface


logger = Logger.getlogger()

def get_project_values(selected_project):
    initial_project_form = {}
    project = None
    if selected_project:
        try:
            project = Project.objects.get(project_name=selected_project)
            initial_project_form = {
                'projects': project.project_name,
                'project_name': project.project_name,
                'crew_name': project.crew_name,
                'planned_vp': project.planned_vp,
                'planned_receivers': project.planned_receivers,
                'planned_start_date': project.planned_start_date,
                'planned_end_date': project.planned_end_date,
                'standby_rate': project.standby_rate,
                'cap_rate': project.cap_rate,
                'cap_app_ctm': project.cap_app_ctm,
            }

        except Project.DoesNotExist:
            selected_project = ''

    return selected_project, project, initial_project_form


def get_block_values(project, selected_block):
    initial_block_form = {}
    block = None
    if not project:
        return '', block, initial_block_form

    if selected_block:
        try:
            block = Block.objects.get(project=project, block_name=selected_block)

        except Block.DoesNotExist:
            pass

    if not block:
        try:
            block = Block.objects.filter(project=project).first()

        except Block.DoesNotExist:
            pass

    if block:
        selected_block = block.block_name
        initial_block_form = {
            'block_name': block.block_name,
            'block_planned_vp': block.block_planned_vp,
            'block_planned_receivers': block.block_planned_receivers,
            }
        return selected_block, block, initial_block_form

    else:
        return '', block, initial_block_form


def get_sourcetype_values(project, selected_sourcetype_name):
    initial_sourcetype_form = {}
    sourcetype = None
    if not project:
        return '', sourcetype, initial_sourcetype_form

    if selected_sourcetype_name:
        try:
            sourcetype = SourceType.objects.get(
                project=project, sourcetype_name=selected_sourcetype_name)

        except SourceType.DoesNotExist:
            pass

    if not sourcetype:
        try:
            sourcetype = SourceType.objects.filter(project=project).first()

        except SourceType.DoesNotExist:
            pass

    if sourcetype:
        selected_sourcetype_name = sourcetype.sourcetype_name
        initial_sourcetype_form = {
            'sourcetype_name': sourcetype.sourcetype_name,
            'sourcetype': sourcetype.sourcetype,
            'source_spacing': sourcetype.source_spacing,
            'mpr_vibes': sourcetype.mpr_vibes,
            'mpr_sweep_length': sourcetype.mpr_sweep_length,
            'mpr_moveup': sourcetype.mpr_moveup,
            'mpr_rec_hours': sourcetype.mpr_rec_hours,
        }
        return selected_sourcetype_name, sourcetype, initial_sourcetype_form

    else:
        return '', sourcetype, initial_sourcetype_form


@method_decorator(login_required, name='dispatch')
class ProjectView(View):

    form_project_control = ProjectControlForm
    form_block_control = BlockControlForm
    form_sourcetype_control = SourceTypeControlForm
    form_project = ProjectForm
    form_block = BlockForm
    form_sourcetype = SourceTypeForm
    template_project_page = 'daily_report/project_page.html'
    ri = ReportInterface('')
    new_project_name = ''

    def get(self, request):
        selected_project = request.session.get('selected_project', '')
        selected_block = request.session.get('selected_block', '')
        selected_sourcetype = request.session.get('selected_sourcetype', '')

        selected_project, project, initial_project_form = (
            get_project_values(selected_project))
        daily_id, report_date = self.ri.get_latest_report_id(selected_project)
        request.session['report_date'] = date_to_string(report_date)

        selected_block, _, initial_block_form = (
            get_block_values(project, selected_block))

        selected_sourcetype, _, initial_sourcetype_form = (
            get_sourcetype_values(project, selected_sourcetype))

        form_project = self.form_project(initial=initial_project_form)
        form_block = self.form_block(initial=initial_block_form)
        form_sourcetype = self.form_sourcetype(initial=initial_sourcetype_form)

        form_project_control = self.form_project_control(
            initial={
                'projects': selected_project,
                'new_project_name': '',
                'daily_id': daily_id,
                })
        form_block_control = self.form_block_control(
            project=project,
            initial={
                'blocks': selected_block,
                'new_block_name': '',
                })
        form_sourcetype_control = self.form_sourcetype_control(
            project=project,
            initial={
                'sourcetypes': selected_sourcetype,
                'new_sourcetype_name': '', })

        context = {'form_project': form_project,
                   'form_block': form_block,
                   'form_sourcetype': form_sourcetype,
                   'form_project_control': form_project_control,
                   'form_block_control': form_block_control,
                   'form_sourcetype_control': form_sourcetype_control,
                  }

        return render(request, self.template_project_page, context)

    def post(self, request):
        form_project_control = self.form_project_control(request.POST)
        if form_project_control.is_valid():

            # get project controls
            self.selected_project = form_project_control.cleaned_data.get(
                'projects', '')
            self.new_project_name = form_project_control.cleaned_data.get(
                'new_project_name', '')[:NAME_LENGTH]
            self.button_pressed = form_project_control.cleaned_data.get(
                'button_pressed', '')

            #get project object
            _, self.project, _ = get_project_values(self.selected_project)

            # Get the pdf_workorder_file from request
            try:
                pdf_workorder_file = request.FILES['pdf_workorder_file']
                f = open(pdf_workorder_file.temporary_file_path(), 'rb')
                f.seek(0)
                self.project.pdf_work_order = f.read()
                f.close()
                self.project.save()

            except MultiValueDictKeyError:
                pass

            # get block controls
            form_block_control = self.form_block_control(
                request.POST, project=self.project)
            if form_block_control.is_valid():
                self.selected_block = form_block_control.cleaned_data.get('blocks', '')
                self.new_block_name = form_block_control.cleaned_data.get(
                    'new_block_name', '')[:NAME_LENGTH]

            else:
                self.selected_block = ''
                self.new_block_name = ''

            # get sourcetype controls
            form_sourcetype_control = self.form_sourcetype_control(
                request.POST, project=self.project)
            if form_sourcetype_control.is_valid():
                self.selected_sourcetype = form_sourcetype_control.cleaned_data.get(
                    'sourcetypes', '')
                self.new_sourcetype_name = form_sourcetype_control.cleaned_data.get(
                    'new_sourcetype_name', '')[:NAME_LENGTH]

            else:
                self.selected_sourcetype = ''
                self.new_sourcetype_name = ''

            # get block and source type objects
            _, self.block, _ = get_block_values(self.project, self.selected_block)
            _, self.sourcetype, _ = get_sourcetype_values(
                self.project, self.selected_sourcetype)

            # action for project submit button
            if self.button_pressed == 'submit_project':
                form_project = ProjectForm(request.POST, instance=self.project)

                if form_project.is_valid():
                    form_project.save(commit=True)
                    # in case the name of the project has been changed
                    self.selected_project = form_project.cleaned_data.get(
                        'project_name')
                    # disable button pressed
                    self.button_pressed = ''

            # action for block submit button
            if self.button_pressed == 'submit_block':
                form_block = BlockForm(request.POST, instance=self.block)

                if form_block.is_valid():
                    form_block.save(commit=True)
                    # in case the name of the block has been changed
                    self.selected_block = form_block.cleaned_data.get(
                        'block_name')[:NAME_LENGTH]
                    self.button_pressed = ''

            # action for sourcetype submit button
            if self.button_pressed == 'submit_sourcetype':
                form_sourcetype = SourceTypeForm(request.POST, instance=self.sourcetype)

                if form_sourcetype.is_valid():
                    form_sourcetype.save(commit=True)
                    # in case the name of the sourcetype has been changed
                    self.selected_sourcetype = form_sourcetype.cleaned_data.get(
                        'sourcetype_name')[:NAME_LENGTH]
                    self.button_pressed = ''

            # actions for new or delete buttons are pressed
            if self.button_pressed in ['new_project', 'delete_project']:
                self.create_or_delete_project()

            if self.button_pressed in ['new_block', 'delete_block']:
                self.create_or_delete_block()

            if self.button_pressed in ['new_sourcetype', 'delete_sourcetype']:
                self.create_or_delete_sourcetype()

            #get latest values after changes
            self.selected_project, _, initial_project_form = (
                get_project_values(self.selected_project))
            daily_id, report_date = self.ri.get_latest_report_id(self.selected_project)
            request.session['report_date'] = date_to_string(report_date)

            self.selected_block, _, initial_block_form = (
                get_block_values(self.project, self.selected_block))

            self.selected_sourcetype, _, initial_sourcetype_form = (
                get_sourcetype_values(self.project, self.selected_sourcetype))

            form_project = self.form_project(initial=initial_project_form)
            form_block = self.form_block(initial=initial_block_form)
            form_sourcetype = self.form_sourcetype(initial=initial_sourcetype_form)
            form_project_control = self.form_project_control(
                initial={
                    'projects': self.selected_project,
                    'new_project_name': '',
                    'daily_id': daily_id,
                    })
            form_block_control = self.form_block_control(
                project=self.project, initial={
                    'blocks': self.selected_block,
                    'new_block_name': '',
                    })
            form_sourcetype_control = self.form_sourcetype_control(
                project=self.project, initial={
                    'sourcetypes': self.selected_sourcetype,
                    'new_sourcetype_name': '',
                    })
            request.session['selected_project'] = self.selected_project
            request.session['selected_block'] = self.selected_block
            request.session['selected_sourcetype'] = self.selected_sourcetype

        else:
            form_project = self.form_project()
            form_block = self.form_block()
            form_sourcetype = self.form_sourcetype()
            form_project_control = self.form_project_control(initial={
                'projects': '',
                'new_project_name': '',
                'daily_id': 0,
                })
            form_block_control = self.form_block_control(initial={
                'blocks': '',
                'new_block_name': '',
                })
            form_sourcetype_control = self.form_sourcetype_control(initial={
                'sourcetypes': '',
                'new_sourcetype_name': '',
                })
        context = {
            'form_project': form_project,
            'form_block': form_block,
            'form_sourcetype': form_sourcetype,
            'form_project_control': form_project_control,
            'form_block_control': form_block_control,
            'form_sourcetype_control': form_sourcetype_control,
        }

        return render(request, self.template_project_page, context)

    def create_or_delete_project(self):
        if self.button_pressed == 'new_project':
            try:
                self.project = Project.objects.create(
                    project_name=self.new_project_name
                )
                self.selected_project = self.new_project_name

            except IntegrityError:
                self.project = None

            self.new_project_name = ''

        elif self.button_pressed == 'delete_project':
            if not self.project:
                return

            self.project.delete()
            self.project = None
            self.selected_project = ''
            self.new_project_name = ''

        else:
            pass

        self.button_pressed = ''

    def create_or_delete_block(self):
        if self.button_pressed == 'new_block':
            try:
                self.block = Block.objects.create(
                    project=self.project,
                    block_name=self.new_block_name
                )
                self.selected_block = self.new_block_name

            except IntegrityError:
                pass

            self.new_block_name = ''

        elif self.button_pressed == 'delete_block':
            if not self.block:
                return

            self.block.delete()
            self.block = None
            self.selected_block = ''
            self.new_block_name = ''

        else:
            pass

        self.button_pressed = ''

    def create_or_delete_sourcetype(self):
        if self.button_pressed == 'new_sourcetype':
            try:
                self.sourcetype = SourceType.objects.create(
                    project=self.project,
                    sourcetype_name=self.new_sourcetype_name
                )
                self.selected_sourcetype = self.new_sourcetype_name

            except IntegrityError:
                pass

            self.new_sourcetype_name = ''

        elif self.button_pressed == 'delete_sourcetype':
            if not self.sourcetype:
                return

            self.sourcetype.delete()
            self.sourcetype = None
            self.selected_sourcetype = ''
            self.new_sourcetype_name = ''

        else:
            pass

        self.button_pressed = ''


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


def download_pdf_workorder(request, project_name):
    project = Project.objects.get(project_name=project_name)
    f_pdf = io.BytesIO(project.pdf_work_order.tobytes())
    f_pdf.seek(0)
    return FileResponse(f_pdf, content_type='application/pdf', as_attachment=False)
