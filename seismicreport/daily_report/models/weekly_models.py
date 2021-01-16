from django.db import models
from daily_report.models.project_models import Project
from daily_report.models.daily_models import Person
from seismicreport.vars import COMMENT_LENGTH


class Weekly(models.Model):
    week_report_date = models.DateField()
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='weeklies')
    author = models.ForeignKey(
        Person, on_delete=models.CASCADE, related_name='weeklies', blank=True, null=True)
    csr_week_comment = models.TextField(max_length=COMMENT_LENGTH, default='')

    def __str__(self):
        return f'weekly: {self.week_report_date} - project: {self.project.project_name}'

    class Meta:
        unique_together = ['week_report_date', 'project']
