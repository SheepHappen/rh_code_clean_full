from django import forms

from allauth.account.forms import LoginForm
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, HTML, Submit, ButtonHolder, Field

from riskfactor.models import RiskDataSet
from .models import ManagementQuestion, DocumentQuestion


class ShowHidePasswordField(Field):
    template = 'form/toggle_password_visibility.html'


class ManagementQuestionForm(forms.ModelForm):
    risk_factors = forms.ModelMultipleChoiceField(
        required=True,
        queryset=RiskDataSet.objects.all()
    )

    class Meta:
        model = ManagementQuestion
        fields = (
            'category',
            'company',
            'text',
        )

    def __init__(self, *args, **kwargs):
        if kwargs.get('instance'):
            initial = kwargs.setdefault('initial', {})
            initial['risk_factors'] = kwargs['instance'].riskfactors.all().values_list('pk', flat=True)

        forms.ModelForm.__init__(self, *args, **kwargs)

    def save(self, commit=True):
        instance = forms.ModelForm.save(self, False)

        def save_m2m():
            instance.riskfactors.clear()
            instance.riskfactors.add(*self.cleaned_data['risk_factors'])

        self.save_m2m = save_m2m

        if commit:
            instance.save()
            self.save_m2m()

        return instance

    helper = FormHelper()
    helper.form_tag = False

    helper.layout = Layout(
        'category',
        'company',
        'text',
        'risk_factors',
        ButtonHolder(
            Submit('submit', 'Submit'),
            HTML('<a class="btn btn-primary ml-4" href="/">Cancel</a>')
        ),
    )


class DocumentQuestionForm(forms.ModelForm):
    class Meta:
        model = DocumentQuestion
        fields = (
            'category',
            'text',
            'company',
            'trigger_question',
            'yes_score',
            'no_score',
            'pdf_display_order',
            'pdf_display_name'
        )

    helper = FormHelper()
    helper.form_tag = False

    helper.layout = Layout(
        'category',
        'text',
        'trigger_question',
        'yes_score',
        'no_score',
        'pdf_display_order',
        'pdf_display_name',
        ButtonHolder(
            Submit('submit', 'Submit'),
            HTML('<a class="btn btn-primary ml-4" href="/">Cancel</a>')
        ),
    )

    def clean_trigger_question(self):
        if self.cleaned_data.get('trigger_question'):
            trigger = self.cleaned_data['trigger_question']
            if trigger.trigger_question_id:
                raise forms.ValidationError("Questions should only be 1 level down")

            return trigger


class AxesLoginForm(LoginForm):
    def user_credentials(self):
        credentials = super().user_credentials()
        credentials['login'] = credentials.get('email')
        return credentials
