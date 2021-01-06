from django import forms
from daily_report.models.project_models import Project, Block, SourceType
from seismicreport.vars import NAME_LENGTH, TYPE_LENGTH


class ProjectControlForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(ProjectControlForm, self).__init__(*args, **kwargs)

        self.fields['button_pressed'] = forms.CharField(required=False)

        # project form fields
        project_choices = [
            (project.project_name, project.project_name)
            for project in Project.objects.all().order_by('project_name')]

        self.fields['projects'] = forms.ChoiceField(
            widget=forms.Select(),
            choices=project_choices,
            required=False,)

        self.fields['new_project_name'] = forms.CharField(
            max_length=NAME_LENGTH, required=False)

        self.fields['report_date'] = forms.CharField(required=False)

        self.fields['daily_id'] = forms.IntegerField(required=False)


class BlockControlForm(forms.Form):
    def __init__(self, *args, **kwargs):
        project = kwargs.pop('project', 0)
        super(BlockControlForm, self).__init__(*args, **kwargs)

        block_choices = [
            (block.block_name, block.block_name)
            for block in Block.objects.filter(project=project).order_by('block_name')]

        self.fields['blocks'] = forms.ChoiceField(
            widget=forms.Select(),
            choices=block_choices,
            required=False,)

        self.fields['new_block_name'] = forms.CharField(
            max_length=NAME_LENGTH, required=False)


class SourceTypeControlForm(forms.Form):
    def __init__(self, *args, **kwargs):
        project = kwargs.pop('project', 0)
        super(SourceTypeControlForm, self).__init__(*args, **kwargs)

        st_choices = [
            (st.sourcetype_name, st.sourcetype_name)
            for st in SourceType.objects.filter(project=project).order_by(
                'sourcetype_name')]

        self.fields['sourcetypes'] = forms.ChoiceField(
            widget=forms.Select(),
            choices=st_choices,
            required=False,)

        self.fields['new_sourcetype_name'] = forms.CharField(
            max_length=NAME_LENGTH, required=False)


class ProjectForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(ProjectForm, self).__init__(*args, **kwargs)

        self.fields['project_name'] = forms.CharField(
            max_length=NAME_LENGTH, required=False)
        self.fields['crew_name'] = forms.CharField(
            max_length=NAME_LENGTH, required=False)
        self.fields['planned_area'] = forms.FloatField(required=False)
        self.fields['planned_vp'] = forms.IntegerField(required=False)
        self.fields['planned_receivers'] = forms.IntegerField(required=False)
        self.fields['planned_start_date'] = forms.DateField(required=False)
        self.fields['planned_end_date'] = forms.DateField(required=False)
        self.fields['standby_rate'] = forms.FloatField(required=False)
        self.fields['cap_rate'] = forms.FloatField(required=False)
        self.fields['cap_app_ctm'] = forms.FloatField(
            label='Cap app/ctm', required=False)

    class Meta:
        model = Project
        fields = (
            'project_name', 'crew_name', 'planned_area',
            'planned_vp', 'planned_receivers',
            'planned_start_date', 'planned_end_date',
            'standby_rate', 'cap_rate', 'cap_app_ctm'
        )


class BlockForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(BlockForm, self).__init__(*args, **kwargs)

        self.fields['block_name'] = forms.CharField(
            max_length=NAME_LENGTH, required=False)
        self.fields['block_planned_area'] = forms.FloatField(required=False)
        self.fields['block_planned_vp'] = forms.IntegerField(required=False)
        self.fields['block_planned_receivers'] = forms.IntegerField(required=False)

    class Meta:
        model = Block
        fields = (
            'block_name', 'block_planned_area', 'block_planned_vp',
            'block_planned_receivers',
        )


class SourceTypeForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(SourceTypeForm, self).__init__(*args, **kwargs)

        self.fields['sourcetype_name'] = forms.CharField(
            max_length=NAME_LENGTH, label='source type name', required=False)
        self.fields['sourcetype'] = forms.CharField(
            max_length=TYPE_LENGTH, label='source type', required=False)
        self.fields['sourcepoint_spacing'] = forms.FloatField(required=False)
        self.fields['sourceline_spacing'] = forms.FloatField(required=False)
        self.fields['mpr_vibes'] = forms.IntegerField(
            label='mpr vibes', required=False)
        self.fields['mpr_sweep_length'] = forms.IntegerField(
            label='mpr sweep length', required=False)
        self.fields['mpr_moveup'] = forms.IntegerField(
            label='mpr moveup', required=False)
        self.fields['mpr_rec_hours'] = forms.FloatField(
            label='mpr recording hours', required=False)

    class Meta:
        model = SourceType
        fields = (
            'sourcetype_name', 'sourcetype', 'sourcepoint_spacing', 'sourceline_spacing',
            'mpr_vibes', 'mpr_sweep_length', 'mpr_moveup', 'mpr_rec_hours',
        )
