from users.models import User
from django import forms

from accounts.models import UserProfile
from company.models import Company


class UserEditForm(forms.ModelForm):
    job_title = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={'placeholder': 'Job title'}),
        required=False
    )
    phone_number = forms.CharField(
        max_length=64,
        widget=forms.TextInput(attrs={'placeholder': 'Phone number'}),
        required=False
    )
    avatar = forms.ImageField(
        required=False
    )
    company = forms.ChoiceField(label='Company', required=False)

    class Meta:
        model = User
        fields = (
            'email',
            'first_name',
            'last_name',
            'job_title',
            'phone_number',
            'avatar',
            'company'
        )

    def __init__(self, *args, **kwargs):
        super(UserEditForm, self).__init__(*args, **kwargs)
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        if self.instance.is_superuser:
            self.fields['company'].choices = self.get_companies()
        else:
            self.fields['company'].widget = forms.HiddenInput()

        profile = UserProfile.objects.filter(user=self.instance)
        if profile:
            self.fields['job_title'].initial = profile[0].job_title
            self.fields['phone_number'].initial = profile[0].phone_number
            self.fields['avatar'].initial = profile[0].avatar
            if self.instance.is_superuser:
                self.fields['company'].initial = profile[0].company

    def get_companies(self):
        companies = Company.objects.all().order_by('name')
        return [
            (company.name, company.name)
            for company in companies
        ]

    def save(self, commit=True):
        instance = super().save()

        profile, _ = UserProfile.objects.get_or_create(user=instance)

        if self.cleaned_data.get('job_title'):
            profile.job_title = self.cleaned_data['job_title']
        if self.cleaned_data.get('phone_number'):
            profile.phone_number = self.cleaned_data['phone_number']
        if self.cleaned_data.get('avatar'):
            profile.avatar = self.cleaned_data['avatar']
        else:
            profile.avatar = None

        if self.cleaned_data.get('company'):
            profile.company = Company.objects.get(name=self.cleaned_data['company'])
        profile.save()

        return instance
