'''  module for project backend tasks
'''
from django.db.utils import IntegrityError
from django.db.models import ProtectedError
from daily_report.models.project_models import (
    Project, Block, SourceType, ReceiverType,
)
from daily_report.models.daily_models import SourceProduction, ReceiverProduction
from seismicreport.utils.plogger import Logger


logger = Logger.getlogger()


class ProjectInterface:

    def __init__(self):
        pass

    @staticmethod
    def get_project_values(selected_project):
        initial_project_form = {}
        project = None
        if selected_project:
            try:
                project = Project.objects.get(project_name=selected_project)
                initial_project_form = {
                    'projects': project.project_name,
                    'project_name': project.project_name,
                    'start_report': project.start_report,
                    'crew_name': project.crew_name,
                    'planned_area': project.planned_area,
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


    @staticmethod
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
                'block_planned_area': block.block_planned_area,
                'block_planned_vp': block.block_planned_vp,
                'block_planned_receivers': block.block_planned_receivers,
                }
            return selected_block, block, initial_block_form

        else:
            return '', block, initial_block_form

    @staticmethod
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
                'sourcepoint_spacing': sourcetype.sourcepoint_spacing,
                'sourceline_spacing': sourcetype.sourceline_spacing,
                'mpr_vibes': sourcetype.mpr_vibes,
                'mpr_sweep_length': sourcetype.mpr_sweep_length,
                'mpr_moveup': sourcetype.mpr_moveup,
                'mpr_rec_hours': sourcetype.mpr_rec_hours,
            }
            return selected_sourcetype_name, sourcetype, initial_sourcetype_form

        else:
            return '', sourcetype, initial_sourcetype_form

    @staticmethod
    def get_receivertype_values(project, selected_receivertype_name):
        initial_receivertype_form = {}
        receivertype = None
        if not project:
            return '', receivertype, initial_receivertype_form

        if selected_receivertype_name:
            try:
                receivertype = ReceiverType.objects.get(
                    project=project, receivertype_name=selected_receivertype_name)

            except ReceiverType.DoesNotExist:
                pass

        if not receivertype:
            try:
                receivertype = ReceiverType.objects.filter(project=project).first()

            except ReceiverType.DoesNotExist:
                pass

        if receivertype:
            selected_receivertype_name = receivertype.receivertype_name
            initial_receivertype_form = {
                'receivertype_name': receivertype.receivertype_name,
                'receivertype': receivertype.receivertype,
                'receiverpoint_spacing': receivertype.receiverpoint_spacing,
                'receiverline_spacing': receivertype.receiverline_spacing,
                'receivers_per_station': receivertype.receivers_per_station,
                'field_qc_rqrmt': receivertype.field_qc_rqrmt,
                'camp_qc_rqrmt':receivertype.camp_qc_rqrmt,
            }
            return selected_receivertype_name, receivertype, initial_receivertype_form

        else:
            return '', receivertype, initial_receivertype_form

    @staticmethod
    def create_project(new_project_name):
        try:
            project = Project.objects.create(
                project_name=new_project_name
            )
            return project, new_project_name

        except IntegrityError:
            return None, ''

    @staticmethod
    def delete_project(project):
        if project:
            for sourcetype in SourceProduction.objects.filter(daily__project=project):
                sourcetype.delete()

            for receivertype in ReceiverProduction.objects.filter(daily__project=project):
                receivertype.delete()

            for day in project.dailies.all():
                day.delete()

            project.delete()

        return None, ''

    @staticmethod
    def create_block(project, new_block_name):
        if not project:
            return None, ''

        try:
            block = Block.objects.create(
                project=project,
                block_name=new_block_name
            )
            return block, new_block_name

        except IntegrityError:
            return None, ''

    @staticmethod
    def delete_block(block):
        if block:
            try:
                block.delete()

            except ProtectedError:
                logger.info(f'"{block}" is used by daily reports')

        return None, ''

    @staticmethod
    def create_sourcetype(project, new_sourcetype_name):
        if not project:
            return None, ''

        try:
            sourcetype = SourceType.objects.create(
                project=project,
                sourcetype_name=new_sourcetype_name
            )
            return sourcetype, new_sourcetype_name

        except IntegrityError:
            return None, ''

    @staticmethod
    def delete_sourcetype(sourcetype):
        if sourcetype:
            try:
                sourcetype.delete()

            except ProtectedError:
                logger.info(f'sourcetype "{sourcetype}" is used by daily reports')

        return None, ''

    @staticmethod
    def create_receivertype(project, new_receivertype_name):
        if not project:
            return None, ''

        try:
            receivertype = ReceiverType.objects.create(
                project=project,
                receivertype_name=new_receivertype_name
            )
            return receivertype, new_receivertype_name

        except IntegrityError:
            return None, ''

    @staticmethod
    def delete_receivertype(receivertype):
        if receivertype:
            try:
                receivertype.delete()

            except ProtectedError:
                logger.info(f'receivertype "{receivertype}" is used by daily reports')

        return None, ''

    @staticmethod
    def store_workorder(project, pdf_workorder_file):
        if not project:
            return

        f = open(pdf_workorder_file.temporary_file_path(), 'rb')
        f.seek(0)
        project.pdf_work_order = f.read()
        f.close()
        project.save()
