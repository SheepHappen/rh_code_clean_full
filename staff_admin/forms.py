from django import forms

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Submit, ButtonHolder

from core.models import Application
from core.constants import (
    COL_LABELS,
    DATA_ORDER,
    ROW_LABELS,
    SKEW,
)
from riskfactor.models import RiskDataSet, CountryRisk, MaterialityRisk


class UploadForm(forms.Form):
    application = forms.ChoiceField(required=True)
    risk_factor = forms.ChoiceField(required=True)
    reference = forms.CharField(
        label="Data Reference",
        required=False,
        widget=forms.Textarea(
            attrs={
                "rows": 5,
                "cols": 20
            }
        )
    )
    url = forms.URLField(required=False, label="Data URL")
    description = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "rows": 5,
                "cols": 20
            }
        )
    )
    document = forms.FileField(required=True, help_text="(.Xlsx)")
    col_country = forms.ChoiceField(label='Country Column', choices=COL_LABELS, initial=0)
    col_data = forms.ChoiceField(label='Data Column', choices=COL_LABELS, initial=1)
    start_row = forms.ChoiceField(label='Data Start Row', choices=ROW_LABELS)
    normalise_data = forms.BooleanField(
        label='Normalise data',
        required=False,
        initial=True,
        help_text='If your data is already scaled 0-10 for all countries, please untick this box'
    )
    ignore_empty_data = forms.BooleanField(label='Ignore rows with empty data', required=False)
    data_order = forms.ChoiceField(
        label='Data Order',
        choices=DATA_ORDER,
        initial="DESC",
        help_text='Ascending is consistent with raw data, where low values correspond to the worst performing countries, e.g. Air Quality / India = 5.7 and the high values correspond to the best performing countries e.g. Finland equals 99 and India equals 5.75, so data needs reversing'
    )
    skew = forms.ChoiceField(label='Skew', choices=SKEW, initial='NONE', required=False)

    def __init__(self, *args, **kwargs):
        items = kwargs.pop('items', None)
        if items:
            form_type = items.pop('form_type', None)
            need_doc = items.pop('need_doc', None)
        else:
            need_doc = None
            form_type = None
        super().__init__(*args, **kwargs)

        if need_doc == 'No':
            self.fields['document'].required = False
        self.fields['risk_factor'].choices = self.get_risk_factor()
        self.fields['skew'].widget = forms.HiddenInput()
        if form_type == 'Sector':
            self.fields['application'].choices = self.get_applications(exclude='Geographic')
            self.fields['col_data'].widget = forms.HiddenInput()
            self.fields['col_country'].widget = forms.HiddenInput()
            self.fields['risk_factor'].required = False
            self.fields['risk_factor'].widget = forms.HiddenInput()
            self.fields['application'].initial = "sector"
            self.fields['url'].widget = forms.HiddenInput()
            self.fields['data_order'].initial = "ASC"
            self.fields['data_order'].help_text = ""
        else:
            self.fields['application'].choices = self.get_applications(exclude='Sector')
            self.fields['application'].initial = "geographic"

        self.fields['application'].disabled = True

    def get_applications(self, exclude):
        application = Application.objects.all().order_by('name').exclude(name__in=[exclude, 'Value At Risk', 'Commodity'])
        return [
            (app.slug, app.name)
            for app in application
        ]

    def get_risk_factor(self):
        return [(factor.name, factor.name) for factor in RiskDataSet.objects.all()]

    helper = FormHelper()
    helper.form_tag = False

    helper.layout = Layout(
        Field("application"),
        Field("risk_factor"),
        'reference',
        'url',
        'description',
        'col_country',
        'col_data',
        'start_row',
        'normalise_data',
        'ignore_empty_data',
        'skew',
        'data_order',
        'document'
    )


class CountryRiskForm(forms.ModelForm):
    class Meta:
        model = CountryRisk
        fields = ('version', 'country', 'exposure')

    helper = FormHelper()
    helper.form_tag = False

    helper.layout = Layout(
        Field("version"),
        Field("country"),
        'exposure',
        ButtonHolder(Submit('submit', 'Submit')),
    )


class MaterialityRiskForm(forms.ModelForm):
    class Meta:
        model = MaterialityRisk
        fields = (
            'industry',
            'dataset_version',
            'materiality',
            'source'
        )

    helper = FormHelper()
    helper.form_tag = False

    helper.layout = Layout(
        Field("industry"),
        Field("dataset_version"),
        'materiality',
        'source',
        ButtonHolder(Submit('submit', 'Submit')),
    )
