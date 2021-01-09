from django.db import models
from django.db.models import Q
from daily_report.models.project_models import Project
from seismicreport.vars import NAME_LENGTH, DESCR_LENGTH, TYPE_LENGTH


class Service(models.Model):
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='services')
    service_contract = models.CharField(max_length=NAME_LENGTH, null=False)
    description = models.CharField(max_length=DESCR_LENGTH, default='')

    def __str__(self):
        return f'Service: {self.service_contract} for {self.project.project_name}'

    class Meta:
        unique_together = ['service_contract', 'project']


class ServiceTask(models.Model):
    service = models.ForeignKey(
        Service, on_delete=models.CASCADE, related_name='tasks')
    task_name = models.CharField(max_length=NAME_LENGTH, null=False)
    task_description = models.CharField(max_length=DESCR_LENGTH, default='')
    task_unit = models.CharField(max_length=TYPE_LENGTH, default='')

    def get_monthly_task_quantities(self, year, month):
        return self.quantities.filter(Q(date__year=year) & Q(date__month=month))

    def __str__(self):
        return f'{self.service.service_contract}: {self.task_name}'

    class Meta:
        unique_together = ['service', 'task_name']


class TaskQuantity(models.Model):
    task = models.ForeignKey(
        ServiceTask, on_delete=models.CASCADE, related_name='quantities')
    date = models.DateField(null=False)
    quantity = models.FloatField(default=0.0)

    class Meta:
        unique_together = ['task', 'date']

    def __str__(self):
        return (
            f'{self.task.service.service_contract}, '
            f'{self.task.task_name}, '
            f'{self.date}: {self.quantity}'
        )
