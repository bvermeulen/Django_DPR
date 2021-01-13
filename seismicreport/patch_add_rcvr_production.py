import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'seismicreport.settings')
django.setup()

from daily_report.models.project_models import Project, ReceiverType
from daily_report.models.daily_models import Daily, ReceiverProduction
from seismicreport.vars import RECEIVERTYPE_NAME

project = Project.objects.get(project_name='NatihWAZ')
rcvr_type = ReceiverType.objects.get(project=project, receivertype_name=RECEIVERTYPE_NAME)
days = Daily.objects.filter(project=project)

for day in days:
    rp = ReceiverProduction.objects.create(
        daily=day,
        receivertype=rcvr_type,
        layout=0,
        pickup=0,
        qc_field=0.0,
        qc_camp=0.0,
        upload=0,
    )
    print(f'processing: {day}')
