import calendar
from django import forms
from daily_report.models.daily_models import Daily, Person
from seismicreport.vars import NAME_LENGTH, COMMENT_LENGTH

#pylint: disable=line-too-long

class DailyForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(DailyForm, self).__init__(*args, **kwargs)

        self.fields['id'] = forms.IntegerField(disabled=True, widget=forms.HiddenInput(), required=False)
        self.fields['production_date'] = forms.DateField(required=False)
        self.fields['project_name'] = forms.CharField(max_length=NAME_LENGTH, required=False)
        self.fields['block_name'] = forms.CharField(max_length=NAME_LENGTH, required=False)
        self.fields['csr_comment'] = forms.CharField(max_length=COMMENT_LENGTH, required=False, widget=forms.Textarea)
        self.fields['pm_comment'] = forms.CharField(max_length=COMMENT_LENGTH, required=False, widget=forms.Textarea)

        # get staff list order by XGO first and then CSR -
        #TODO DailyForm: bit patch as it relies department is either XG0 or CSR, have a look at it
        person_choices = [
            (person.id, person.name) for person in
            Person.objects.filter(department__startswith='X').order_by('department')
        ]
        person_choices += [
            (person.id, person.name) for person in
            Person.objects.filter(department__startswith='C').order_by('name')
        ]
        try:
            staff_initial = kwargs['initial']['staff']

        except KeyError:
            staff_initial = []


        self.fields['staff'] = forms.MultipleChoiceField(
            choices=person_choices,
            widget=forms.CheckboxSelectMultiple(),
            initial=staff_initial,
        )

    class Meta:
        model = Daily
        exclude = ['project', 'block']
        fields = (
            'id', 'production_date', 'csr_comment', 'pm_comment',
        )


class MonthDaysForm(forms.Form):

    def __init__(self, year, month, *args, **kwargs):
        super(MonthDaysForm, self).__init__(*args, **kwargs)

        for day in range(1, calendar.monthrange(year, month)[1] + 1):
            self.fields[f'{year}-{month:02}-{day:02}'] = forms.FloatField(required=False, )
            self.fields[f'{year}-{month:02}-{day:02}'].widget.attrs['style'] = 'width:33px; border:0px'
