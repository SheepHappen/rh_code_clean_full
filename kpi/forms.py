from django import forms

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Field, HTML, Submit, ButtonHolder, Row

from .models import KeyPerformanceIndicator


class KpiForm(forms.ModelForm):
    class Meta:
        model = KeyPerformanceIndicator
        fields = (
            'aspect',
            'is_kpi',
            'detail',
            'sdg_alignment',
            'related_standard',
            'status',
            'commentary'
        )
        labels = {
            'is_kpi': ('KPI'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['detail'].widget.attrs = {'rows': 5}
        self.fields['commentary'].widget.attrs = {'rows': 5}
