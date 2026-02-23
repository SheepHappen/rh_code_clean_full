from allauth.account.signals import email_confirmed
from allauth.account.forms import (
    LoginForm, SignupForm, ResetPasswordForm, ChangePasswordForm
)

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, HTML, Div, Field

from django import forms
from django.core.mail import send_mail
from django.conf import settings
from django.dispatch import receiver
from django.template.loader import render_to_string

from accounts.models import UserProfile
from company.models import CompanyEmailDomain
from core.forms import ShowHidePasswordField
from users.models import User
from .utils import check_email_domain, validate_email


def send_email(subject, from_email, to_email, template, context=None):
    msg_plain = render_to_string('emails/{}.txt'.format(template), context=context).strip()
    html_msg = render_to_string('emails/{}.html'.format(template), context=context)

    send_mail(
        subject,
        msg_plain,
        from_email,
        to_email,
        html_message=html_msg,
    )


class MyChangePasswordForm(ChangePasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['oldpassword'].widget.attrs['autocomplete'] = "new-password"
        self.fields['password1'].widget.attrs['autocomplete'] = "new-password"
        self.fields['password2'].widget.attrs['autocomplete'] = "new-password"
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Div(ShowHidePasswordField('oldpassword')),
            Div(ShowHidePasswordField('password1')),
            Div(ShowHidePasswordField('password2')),
        )


class MyResetPasswordForm(ResetPasswordForm):
    def clean_email(self):
        email = self.cleaned_data["email"]
        self.users = User.objects.filter(email=email)
        return self.cleaned_data["email"]


class MyAccountLogIn(LoginForm):
    def clean_login(self):
        email = self.cleaned_data['login'].strip()
        email_domain = email.split('@')[1].strip()
        check_email_domain(email_domain)

        return email

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['login'].label = "Email address"
        self.fields['remember'].widget = forms.HiddenInput()
        self.fields['password'].widget.attrs['autocomplete'] = "new-password"
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            'login',
            Div(ShowHidePasswordField('password')),
        )


class MyAccountSignUp(SignupForm):
    user_name = forms.CharField(max_length=30)
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    terms_accepted = forms.BooleanField(initial=False, required=True, label='I agree to the <a href="/">Terms & Conditions</a>')
    job_title = forms.CharField(max_length=2550)
    phone = forms.CharField(max_length=64)

    password_help_text = "<small>{}</small>".format("<br>".join([
        "Your password can't be too similar to your other personal information.",
        "Your password must contain at least 12 characters.",
        "Your password can't be a commonly used password.",
        "Your password must contain a lower case character, upper case character number and a special character eg @",
    ]))

    field_order = ['email', 'user_name', 'first_name', 'last_name', 'job_title', 'phone', 'password1', 'password2', 'terms_accepted']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].label = "Email"
        self.fields['email'].widget.attrs['placeholder'] = ''

        self.fields['password2'].widget.attrs['placeholder'] = 'Password'
        self.fields['password2'].widget.attrs['autocomplete'] = "new-password"
        self.fields['password1'].widget.attrs['autocomplete'] = "new-password"
        self.fields['password1'].help_text = self.password_help_text
        self.fields['user_name'].label = 'Username'

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            'email',
            'user_name',
            'first_name',
            'last_name',
            'job_title',
            'phone',
            Div(ShowHidePasswordField('password1')),
            Div(ShowHidePasswordField('password2')),
        )

    def clean_email(self):
        email = self.cleaned_data['email']
        validate_email(email)

        return email

    def custom_signup(self, request, user):
        user.username = self.cleaned_data['user_name']
        user.save()
        job_title = self.cleaned_data['job_title']
        phone = self.cleaned_data['phone']

        email_domain = user.email.split("@")[1].strip()
        company = CompanyEmailDomain.objects.get(domain=email_domain).company

        UserProfile.objects.create(
            company=company,
            user=user,
            job_title=job_title,
            phone_number=phone
        )

        user_mail_template_context = {
            'name': user.get_full_name,
            'email': user.email,
            'company': user.userprofile.company.name,
            'url': request.build_absolute_uri(user.get_admin_url())
        }

        if not settings.SIGN_UP_NOTIFICATION_TO_ADDRESS:
            send_email(
                '{} has just registered'.format(user.email),
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                'notification',
                user_mail_template_context
            )
        else:
            send_email(
                '{} has just registered'.format(user.email),
                settings.DEFAULT_FROM_EMAIL,
                [settings.SIGN_UP_NOTIFICATION_TO_ADDRESS],
                'notification',
                user_mail_template_context
            )


@receiver(email_confirmed)
def email_confirmed_(request, email_address, **kwargs):
    user = email_address.user
    user.is_active = False
    user.save()
