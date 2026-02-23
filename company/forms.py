from django import forms

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, HTML, Submit, ButtonHolder, Div

from .models import Industry, CompanyAssessment, Company


class IndustryForm(forms.ModelForm):
    class Meta:
        model = Industry
        fields = (
            'name',
            'description',
            'short_description',
        )

    helper = FormHelper()
    helper.form_tag = False

    helper.layout = Layout(
        'name',
        'description',
        'short_description',
        ButtonHolder(
            Submit('submit', 'Submit'),
            HTML('<a class="btn btn-primary ml-4" href="/">Cancel</a>')
        ),
    )


class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = (
            'name',
        )

    helper = FormHelper()
    helper.form_tag = False

    helper.layout = Layout(
        'name',
        ButtonHolder(
            Submit('submit', 'Submit'),
            HTML('<a class="btn btn-primary ml-4" href="/">Cancel</a>')
        ),
    )


class KeyDetailsForm(forms.ModelForm):
    class Meta:
        model = CompanyAssessment
        fields = (
            'report_name',
            'company_fund',
            'deal_type',
            'company_name',
            'company_headquarters',
            'company_employee_count',
            'website',
            'company_description',
            'client_reference',
            'report_reference'
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        try:
            funds = self.get_funds(self.instance.created_by)
        except:
            funds = self.get_funds(self.initial['created_by'])

        self.fields['company_fund'].label = "Included in fund"
        self.fields['company_description'].widget.attrs['style'] = "width:886px; height:127px"
        self.fields['company_description'].widget.attrs['placeholder'] = 'Enter text...'
        self.helper = FormHelper()
        self.helper.form_tag = False

        if funds:
            self.fields['company_fund'].choices = funds

            self.helper.layout = Layout(
                Field("company_name"),
                Field("report_name"),
                Field("company_fund", wrapper_class='optional', css_class="col-6"),
                Field("deal_type", wrapper_class='optional', css_class="col-6"),
                Field("company_headquarters", wrapper_class='optional'),
                Field("company_employee_count", wrapper_class='optional'),
                Field("website", wrapper_class='optional'),
                Field("company_description", wrapper_class='optional'),
                Field("client_reference", wrapper_class='optional'),
                Field('report_reference',  wrapper_class='optional'),
            )
        else:
            self.fields.pop('company_fund')
            self.helper.layout = Layout(
                Field("company_name"),
                Field("report_name"),
                Field("deal_type", wrapper_class='optional', css_class="col-6"),
                Field("company_headquarters", wrapper_class='optional'),
                Field("company_employee_count", wrapper_class='optional'),
                Field("website", wrapper_class='optional'),
                Field("company_description", wrapper_class='optional'),
                Field("client_reference", wrapper_class='optional'),
                Field('report_reference',  wrapper_class='optional'),
            )

    def get_funds(self, user):
        try:
            funds = user.userprofile.company.companyfund_set.all()

            return [(None, None)] + [
                (fund.id, fund.name)
                for fund in funds if fund.enabled
            ]
        except:
            return [(None, None)]

    def clean_company_fund(self):
        fund = self.cleaned_data.get("company_fund")
        if fund:
            return fund

    def save(self, commit=True):
        instance = super().save(commit=False)

        instance.created_by = self.initial['created_by']

        if commit:
            instance.save()

        return instance


class CompanyIndustryForm(forms.ModelForm):
    class Meta:
        model = CompanyAssessment
        fields = (
            'industries',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['industries'].widget.attrs['style'] = "width:100%"
        self.fields['industries'].label = ""

    helper = FormHelper()
    helper.form_tag = False

    helper.layout = Layout(
        Field("industries"),
    )


class CompanyFootprintForm(forms.ModelForm):
    class Meta:
        model = CompanyAssessment
        fields = (
            'industries',
            'material_risks',
            'countries',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['material_risks'].widget.attrs['style'] = "width:100%"
        self.fields['material_risks'].help_text = "This is populated by the industries selected above. Additional risks can be selected by typing."
        self.fields['material_risks'].required = True
        self.fields['industries'].widget.attrs['style'] = "width:100%"
        self.fields['industries'].help_text = "Which industries best describe the company's operation? Additional industries can be selected by typing."
        self.fields['industries'].required = True
        self.fields['countries'].widget.attrs['style'] = "width:100%"
        self.fields['countries'].required = True

        if self.instance:
            self.initial['material_risks'] = []

    helper = FormHelper()
    helper.form_tag = False

    helper.layout = Layout(
        Field("industries"),
        Field("material_risks"),
        Field("countries"),
    )


class RecommendationForm(forms.ModelForm):
    class Meta:
        model = CompanyAssessment
        fields = (
            'risk_summary',
            'issues',
            'issue_extra_title',
            'issue_extra_description'
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['risk_summary'].widget.attrs['style'] = "height:127px"
        self.fields['risk_summary'].widget.attrs['cols'] = 200
        self.fields['risk_summary'].widget.attrs['readonly'] = True
        self.fields['risk_summary'].label = 'Overall risk assessment summary'

        self.fields['issues'].widget.attrs['style'] = "width:100%"
        self.fields['issues'].label = "Issues for further consideration"

        if self.instance:
            self.initial['issues'] = []

        self.fields['issue_extra_title'].label = ""
        self.fields['issue_extra_title'].widget.attrs['placeholder'] = "Custom recommendations"
        self.fields['issue_extra_description'].widget.attrs['maxlength'] = "540"
        self.fields['issue_extra_description'].widget.attrs['rows'] = "7"
        self.fields['issue_extra_description'].label = ""

        self.helper = FormHelper()
        self.helper.form_tag = False

        recommendations_title = self.instance.issue_extra_title or "Custom recommendations"
        self.helper.layout = Layout(
            Field("risk_summary"),
            Field("issues", wrapper_class='optional'),
            Div(
                HTML(f'<label>{recommendations_title} <a href="javascript:;">(Edit)</a></label>'),
                css_class="custom-recommendations-title"
            ),
            Field("issue_extra_title", wrapper_class='required custom-recommendations-edit'),
            Div(
                HTML('<span style="position: absolute; right: 0; top: -20px; font-size: 0.8rem;">540 characters maximum</span>'),
                Field("issue_extra_description", wrapper_class='optional'),
                style="position: relative;"
            )
        )
