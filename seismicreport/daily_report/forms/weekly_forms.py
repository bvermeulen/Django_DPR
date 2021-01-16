from django import forms
from daily_report.models.daily_models import Person
from daily_report.models.weekly_models import Weekly
from seismicreport.vars import NAME_LENGTH, COMMENT_LENGTH

#pylint: disable=line-too-long

class WeeklyForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(WeeklyForm, self).__init__(*args, **kwargs)

        self.fields['week_start_date'] =  forms.DateField(required=False)
        self.fields['week_report_date'] = forms.DateField(required=False)
        self.fields['proj_name'] = forms.CharField(max_length=NAME_LENGTH, required=False)
        self.fields['proj_vps'] = forms.IntegerField(required=False)
        self.fields['proj_area'] = forms.FloatField(required=False)
        self.fields['proj_start'] = forms.DateField(required=False)
        self.fields['proj_crew'] = forms.CharField(max_length=NAME_LENGTH, required=False)
        self.fields['csr_week_comment'] = forms.CharField(max_length=COMMENT_LENGTH, required=False, widget=forms.Textarea)

        author_choices = [
            (person.id, person.name) for person in
            Person.objects.filter(department__startswith='C').order_by('name')
        ]
        try:
            author_initial = kwargs['initial']['author']

        except KeyError:
            author_initial = []

        self.fields['author'] = forms.ChoiceField(
            choices=author_choices,
            widget=forms.RadioSelect(),
            initial=author_initial,
            required=False,
        )

    class Meta:
        model = Weekly
        exclude = ['project']
        fields = (
            'week_report_date', 'csr_week_comment'
        )
