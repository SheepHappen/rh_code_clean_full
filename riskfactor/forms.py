from django import forms

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, ButtonHolder

from riskfactor.models import RiskDataSet


class RiskDataSetForm(forms.ModelForm):
    update_due = forms.DateField(
        widget=forms.TextInput(
            attrs={'type': 'date'}
        )
    )

    class Meta:
        model = RiskDataSet
        fields = (
            'name',
            'category',
            'applications',
            'description',
            'pdf_description',
            'recommendation',
            'abbreviated_recommendation',
            'update_due',
            'update_status',
            'notes',
            'active_version'
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.id:
            if self.fields['update_status'].initial == 'r':
                self.fields['update_status'].disabled = True
            elif self.fields['update_status'].initial == 'o':
                self.fields['update_status'].disabled = True
            elif self.fields['update_status'].initial == 'p':
                self.fields['update_status'].disabled = False
                if self.instance.versions:
                    self.fields['active_version'].choices = self.get_versions(self.instance)
            else:
                self.fields['active_version'].widget = forms.HiddenInput()
        else:
            self.fields['active_version'].widget = forms.HiddenInput()
            self.fields['update_status'].required = False
            self.fields['update_status'].widget = forms.HiddenInput()

    def get_versions(self, instance):
        return [
            (version.name, version.name)
            for version in instance.versions.all()
        ]

    helper = FormHelper()
    helper.form_tag = False

    helper.layout = Layout(
        'name',
        'category',
        'applications',
        'description',
        'pdf_description',
        'active_version',
        'recommendation',
        'abbreviated_recommendation',
        'update_due',
        'update_status',
        'notes',
        ButtonHolder(Submit('submit', 'Submit')),
    )
