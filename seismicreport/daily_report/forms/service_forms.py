import calendar
from django import forms


class MonthDaysForm(forms.Form):

    def __init__(self, year, month, *args, **kwargs):
        super(MonthDaysForm, self).__init__(*args, **kwargs)

        for day in range(1, calendar.monthrange(year, month)[1] + 1):
            self.fields[f'{year}-{month:02}-{day:02}'] = forms.FloatField(required=False)
            self.fields[f'{year}-{month:02}-{day:02}'].widget.attrs[
                'style'] = 'width:33px; border:0px'
