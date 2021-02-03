import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'seismicreport.settings')
django.setup()

from daily_report.models.daily_models import Daily
from daily_report.models.project_models import Project
from daily_report.excel_mpr_backend import ExcelMprReport
project = Project.objects.get(project_name='19GL')
day = Daily.objects.get(production_date='2020-5-15', project=project)
xl = ExcelMprReport(day)
xl.collate_mpr_data()

