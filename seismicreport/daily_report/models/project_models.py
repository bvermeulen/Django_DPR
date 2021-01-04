from django.db import models
from django.db.models import Q
from seismicreport.vars import NAME_LENGTH, DESCR_LENGTH, TYPE_LENGTH


class Project(models.Model):
    project_name = models.CharField(max_length=NAME_LENGTH, unique=True, )
    crew_name = models.CharField(max_length=NAME_LENGTH, default='')
    pdf_work_order = models.BinaryField()
    planned_area = models.FloatField(default=0.0)
    planned_vp = models.IntegerField(default=0)
    planned_receivers = models.IntegerField(default=0)
    planned_start_date = models.DateField(null=True)
    planned_end_date = models.DateField(null=True)

    # In case app/ctm > 100% then an extra rate is due which is capped
    # at mpr_ratecap (e.g. 105%) at mpr_app_ctm_cap (e.g. 110%).
    # Values are prorated for app/ctm between 100% and mpr_app_ctm_cap
    standby_rate = models.FloatField(default=0)
    cap_rate = models.FloatField(default=0)
    cap_app_ctm = models.FloatField(default=0)

    def __str__(self):
        return str(self.project_name)


class Block(models.Model):
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='blocks')
    block_name = models.CharField(max_length=NAME_LENGTH, null=False)
    block_shapefile = models.BinaryField()
    block_planned_area = models.FloatField(default=0.0)
    block_planned_vp = models.IntegerField(default=0)
    block_planned_receivers = models.IntegerField(default=0)

    class Meta:
        unique_together = ['block_name', 'project']

    def __str__(self):
        return f'{self.project.project_name}: {self.block_name}'


class SourceType(models.Model):
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='sourcetypes')
    sourcetype_name = models.CharField(max_length=NAME_LENGTH, null=False)
    sourcetype = models.CharField(max_length=TYPE_LENGTH, null=False)
    sourcepoint_spacing = models.FloatField(default=0.0)
    sourceline_spacing = models.FloatField(default=0.0)
    mpr_vibes = models.IntegerField(default=0)
    mpr_sweep_length = models.IntegerField(default=0)
    mpr_moveup = models.IntegerField(default=0)
    mpr_rec_hours = models.FloatField(default=0.0)

    def __str__(self):
        return f'{self.project.project_name}: {self.sourcetype_name}'

    class Meta:
        unique_together = ['sourcetype_name', 'project']


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
