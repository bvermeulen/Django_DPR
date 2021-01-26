from django.db import models
from seismicreport.vars import NAME_LENGTH, TYPE_LENGTH


class Project(models.Model):
    project_name = models.CharField(max_length=NAME_LENGTH, unique=True, )
    crew_name = models.CharField(max_length=NAME_LENGTH, default='')
    start_report = models.DateField(null=True)
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


class ReceiverType(models.Model):
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='receivertypes')
    receivertype_name = models.CharField(max_length=NAME_LENGTH, null=False)
    receivertype = models.CharField(max_length=TYPE_LENGTH, null=False)
    receiverpoint_spacing = models.FloatField(default=0.0)
    receiverline_spacing = models.FloatField(default=0.0)
    receivers_per_station = models.IntegerField(default=0)
    receiver_diagram = models.BinaryField()

    # quality control thresholds
    # number of receivers to be qc'd per day in the field
    field_qc_rqrmt = models.FloatField(default=0.0)
    # number of receivers to  be qc'd per month in camp
    camp_qc_rqrmt = models.FloatField(default=0.0)

    def __str__(self):
        return f'{self.project.project_name}: {self.receivertype_name}'

    class Meta:
        unique_together = ['receivertype_name', 'project']
