from django.db import models
from daily_report.models.project_models import Project, Block, SourceType
from seismicreport.vars import NAME_LENGTH, DESCR_LENGTH, COMMENT_LENGTH


class Person(models.Model):
    name = models.CharField(max_length=NAME_LENGTH, default='', unique=True)
    department = models.CharField(max_length=NAME_LENGTH, default='')

    def __str__(self):
        return f'Name: {self.name}, department: {self.department}'


class Daily(models.Model):
    production_date = models.DateField()
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='dailies')
    block = models.ForeignKey(
        Block, on_delete=models.CASCADE, related_name='dailies', blank=True, null=True)
    staff = models.ManyToManyField(Person, related_name='dailies')
    csr_comment = models.TextField(max_length=COMMENT_LENGTH, default='')
    pm_comment = models.TextField(max_length=COMMENT_LENGTH, default='')

    def __str__(self):
        return f'daily: {self.production_date} - project: {self.project.project_name}'

    class Meta:
        # possible to have two daily reports for two different projects
        unique_together = ['production_date', 'project']


class SourceProduction(models.Model):
    daily = models.ForeignKey(Daily, on_delete=models.CASCADE)
    sourcetype = models.ForeignKey(SourceType, on_delete=models.CASCADE)
    sp_t1_flat = models.IntegerField(default=0)
    sp_t2_rough = models.IntegerField(default=0)
    sp_t3_facilities = models.IntegerField(default=0)
    sp_t4_dunes = models.IntegerField(default=0)
    sp_t5_sabkha = models.IntegerField(default=0)
    skips = models.IntegerField(default=0)

    def __str__(self):
        return f'{self.daily.production_date} - {self.sourcetype.sourcetype_name}'

    class Meta:
        unique_together = ['daily', 'sourcetype']


class TimeBreakdown(models.Model):
    daily = models.OneToOneField(Daily, on_delete=models.CASCADE)
    rec_hours = models.FloatField(default=0)
    rec_moveup = models.FloatField(default=0)
    logistics = models.FloatField(default=0)
    camp_move = models.FloatField(default=0)
    wait_source = models.FloatField(default=0)
    wait_layout = models.FloatField(default=0)
    wait_shift_change = models.FloatField(default=0)
    company_suspension = models.FloatField(default=0)
    company_tests = models.FloatField(default=0)
    beyond_control = models.FloatField(default=0)
    line_fault = models.FloatField(default=0)
    instrument_fault = models.FloatField(default=0)
    vibrator_fault = models.FloatField(default=0)
    incident = models.FloatField(default=0)
    holiday = models.FloatField(default=0)
    recovering = models.FloatField(default=0)
    other_downtime = models.FloatField(default=0)

    def __str__(self):
        return f'timebreakdown for : {self.daily.production_date}'


class HseWeather(models.Model):
    daily = models.OneToOneField(Daily, on_delete=models.CASCADE)
    stop = models.IntegerField(default=0)
    lti = models.IntegerField(default=0)
    fac = models.IntegerField(default=0)
    mtc = models.IntegerField(default=0)
    rwc = models.IntegerField(default=0)
    incident_nm = models.IntegerField(default=0)
    medevac = models.IntegerField(default=0)
    drills = models.IntegerField(default=0)
    audits = models.IntegerField(default=0)
    lsr_violations = models.IntegerField(default=0)
    ops_time = models.FloatField(default=0)
    day_time = models.FloatField(default=0)
    weather_condition = models.CharField(max_length=NAME_LENGTH, default='')
    rain = models.CharField(max_length=NAME_LENGTH, default='')
    temp_min = models.FloatField(default=0)
    temp_max = models.FloatField(default=0)

    def __str__(self):
        return f'HSE/ Weather: {self.daily.production_date}'


class ToolBox(models.Model):
    hse = models.ForeignKey(
        HseWeather, related_name='toolboxes', on_delete=models.CASCADE
    )
    toolbox = models.TextField(max_length=DESCR_LENGTH, default='')

    def __str_(self):
        return f'Toolbox for {self.hse.daily.project}: {self.toolbox:20} ...'
