import io
from django.shortcuts import render
from django.http import FileResponse
from django.utils.decorators import method_decorator
from django.utils.datastructures import MultiValueDictKeyError
from django.contrib.auth.decorators import login_required
from django.views.generic import View
from daily_report.forms.project_forms import (
    ProjectControlForm, BlockControlForm, SourceTypeControlForm, ReceiverTypeControlForm,
    ProjectForm, BlockForm, SourceTypeForm, ReceiverTypeForm
)
from daily_report.models.project_models import Project
from daily_report.project_backend import ProjectInterface
from daily_report.report_backend import ReportInterface
from seismicreport.utils.utils_funcs import date_to_string
from seismicreport.utils.plogger import Logger
from seismicreport.utils.get_ip import get_client_ip
from seismicreport.vars import NAME_LENGTH


logger = Logger.getlogger()


@method_decorator(login_required, name='dispatch')
class ProjectView(View):

    form_project_control = ProjectControlForm
    form_block_control = BlockControlForm
    form_sourcetype_control = SourceTypeControlForm
    form_receivertype_control = ReceiverTypeControlForm
    form_project = ProjectForm
    form_block = BlockForm
    form_sourcetype = SourceTypeForm
    form_receivertype = ReceiverTypeForm
    template_project_page = 'daily_report/project_page.html'
    ri = ReportInterface('')
    pi = ProjectInterface()
    new_project_name = ''

    def get(self, request):
        selected_project = request.session.get('selected_project', '')
        selected_block = request.session.get('selected_block', '')
        selected_sourcetype = request.session.get('selected_sourcetype', '')
        selected_receivertype = request.session.get('selected_receivertype', '')


        selected_project, project, initial_project_form = (
            self.pi.get_project_values(selected_project))
        daily_id, report_date = self.ri.get_latest_report_id(selected_project)
        request.session['report_date'] = date_to_string(report_date)

        selected_block, _, initial_block_form = (
            self.pi.get_block_values(project, selected_block))

        selected_sourcetype, _, initial_sourcetype_form = (
            self.pi.get_sourcetype_values(project, selected_sourcetype))

        selected_receivertype, _, initial_receivertype_form = (
            self.pi.get_receivertype_values(project, selected_receivertype))

        form_project = self.form_project(initial=initial_project_form)
        form_block = self.form_block(initial=initial_block_form)
        form_sourcetype = self.form_sourcetype(initial=initial_sourcetype_form)
        form_receivertype = self.form_receivertype(initial=initial_receivertype_form)

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
        form_receivertype_control = self.form_receivertype_control(
            project=project,
            initial={
                'receivertypes': selected_receivertype,
                'new_receivertype_name': '', })

        context = {'form_project': form_project,
                   'form_block': form_block,
                   'form_sourcetype': form_sourcetype,
                   'form_receivertype': form_receivertype,
                   'form_project_control': form_project_control,
                   'form_block_control': form_block_control,
                   'form_sourcetype_control': form_sourcetype_control,
                   'form_receivertype_control': form_receivertype_control,
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
            _, self.project, _ = self.pi.get_project_values(self.selected_project)

            # Get the pdf_workorder_file from request and store in project
            try:
                self.pi.store_workorder(self.project, request.FILES['pdf_workorder_file'])

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

            # get receivertype controls
            form_receivertype_control = self.form_receivertype_control(
                request.POST, project=self.project)
            if form_receivertype_control.is_valid():
                self.selected_receivertype = form_receivertype_control.cleaned_data.get(
                    'receivertypes', '')
                self.new_receivertype_name = form_receivertype_control.cleaned_data.get(
                    'new_receivertype_name', '')[:NAME_LENGTH]

            else:
                self.selected_receivertype = ''
                self.new_receivertype_name = ''

            # get block and source, receiver type objects
            _, self.block, _ = self.pi.get_block_values(self.project, self.selected_block)
            _, self.sourcetype, _ = self.pi.get_sourcetype_values(
                self.project, self.selected_sourcetype)
            _, self.receivertype, _ = self.pi.get_receivertype_values(
                self.project, self.selected_receivertype)

            # action for project submit button
            if self.button_pressed == 'submit_project':
                form_project = ProjectForm(request.POST, instance=self.project)

                if form_project.is_valid():
                    form_project.save(commit=True)
                    # in case the name of the project has been changed
                    self.selected_project = form_project.cleaned_data.get('project_name')
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

            # action for receivertype submit button
            if self.button_pressed == 'submit_receivertype':
                form_receivertype = ReceiverTypeForm(
                    request.POST, instance=self.receivertype)

                if form_receivertype.is_valid():
                    form_receivertype.save(commit=True)
                    # in case the name of the receivertype has been changed
                    self.selected_receivertype = form_receivertype.cleaned_data.get(
                        'receivertype_name')[:NAME_LENGTH]
                    self.button_pressed = ''

            # actions for new or delete buttons are pressed
            if self.button_pressed in ['new_project', 'delete_project']:
                self.create_or_delete_project()

            if self.button_pressed in ['new_block', 'delete_block']:
                self.create_or_delete_block()

            if self.button_pressed in ['new_sourcetype', 'delete_sourcetype']:
                self.create_or_delete_sourcetype()

            if self.button_pressed in ['new_receivertype', 'delete_receivertype']:
                self.create_or_delete_receivertype()

            #get latest values after changes
            self.selected_project, _, initial_project_form = (
                self.pi.get_project_values(self.selected_project))
            daily_id, report_date = self.ri.get_latest_report_id(self.selected_project)
            request.session['report_date'] = date_to_string(report_date)

            self.selected_block, _, initial_block_form = (
                self.pi.get_block_values(self.project, self.selected_block))

            self.selected_sourcetype, _, initial_sourcetype_form = (
                self.pi.get_sourcetype_values(self.project, self.selected_sourcetype))

            self.selected_receivertype, _, initial_receivertype_form = (
                self.pi.get_receivertype_values(self.project, self.selected_receivertype))

            form_project = self.form_project(initial=initial_project_form)
            form_block = self.form_block(initial=initial_block_form)
            form_sourcetype = self.form_sourcetype(initial=initial_sourcetype_form)
            form_receivertype = self.form_receivertype(initial=initial_receivertype_form)

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
            form_receivertype_control = self.form_receivertype_control(
                project=self.project, initial={
                    'receivertypes': self.selected_receivertype,
                    'new_receivertype_name': '',
                    })

            request.session['selected_project'] = self.selected_project
            request.session['selected_block'] = self.selected_block
            request.session['selected_sourcetype'] = self.selected_sourcetype
            request.session['selected_receivertype'] = self.selected_receivertype

            logger.info(
                f'user {request.user.username} (ip: {get_client_ip(request)}) '
                f'made changes in project: {self.selected_project}'
            )

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
            form_receivertype_control = self.form_receivertype_control(initial={
                'receivertypes': '',
                'new_receivertype_name': '',
                })

        context = {
            'form_project': form_project,
            'form_block': form_block,
            'form_sourcetype': form_sourcetype,
            'form_receivertype': form_receivertype,
            'form_project_control': form_project_control,
            'form_block_control': form_block_control,
            'form_sourcetype_control': form_sourcetype_control,
            'form_receivertype_control': form_receivertype_control,
        }

        return render(request, self.template_project_page, context)

    def create_or_delete_project(self):
        if self.button_pressed == 'new_project':
            self.project, self.selected_project = self.pi.create_project(
                self.new_project_name
            )

        elif self.button_pressed == 'delete_project':
            self.project, self.selected_project = self.pi.delete_project(self.project)

        self.new_project_name = ''
        self.button_pressed = ''

    def create_or_delete_block(self):
        if self.button_pressed == 'new_block':
            self.block, self.selected_block = self.pi.create_block(
                self.project, self.new_block_name
            )

        elif self.button_pressed == 'delete_block':
            self.block, self.selected_bklock = self.pi.delete_block(self.block)

        self.new_block_name = ''
        self.button_pressed = ''

    def create_or_delete_sourcetype(self):
        if self.button_pressed == 'new_sourcetype':
            self.sourcetype, self.selected_sourcetype = self.pi.create_sourcetype(
                self.project, self.new_sourcetype_name
            )

        elif self.button_pressed == 'delete_sourcetype':
            self.sourcetype, self.selected_sourcetype = self.pi.delete_sourcetype(
                self.sourcetype)

        self.new_sourcetype_name = ''
        self.button_pressed = ''

    def create_or_delete_receivertype(self):
        if self.button_pressed == 'new_receivertype':
            self.receivertype, self.selected_receivertype = self.pi.create_receivertype(
                self.project, self.new_receivertype_name
            )

        elif self.button_pressed == 'delete_receivertype':
            self.receivertype, self.selected_receivertype = self.pi.delete_receivertype(
                self.receivertype)

        self.new_receivertype_name = ''
        self.button_pressed = ''



def download_pdf_workorder(request, project_name):
    project = Project.objects.get(project_name=project_name)
    f_pdf = io.BytesIO(project.pdf_work_order)
    f_pdf.seek(0)
    # note FileResponse will close the file/ buffer - do not use with block
    return FileResponse(f_pdf, content_type='application/pdf', as_attachment=False)
