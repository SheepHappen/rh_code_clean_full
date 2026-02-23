from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.views.generic import DetailView, UpdateView

from allauth.account.views import PasswordChangeView

from accounts.forms import UserEditForm
from users.models import User


class ProfileView(LoginRequiredMixin, DetailView):
    template_name = "profile.html"
    model = User
    context_object_name = 'user'
    slug_url_kwarg = 'slug'
    query_pk_and_slug = True

    def get_object(self):
        return self.request.user


class ProfileEditView(LoginRequiredMixin, UpdateView):
    template_name = "user_edit.html"
    form_class = UserEditForm
    model = User
    slug_url_kwarg = 'slug'
    query_pk_and_slug = True

    def get_object(self):
        return self.request.user

    def get_success_url(self):
        return reverse('profile')


class CustomPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    def get_success_url(self):
        return reverse(
            'profile',
            kwargs={'slug': self.request.user.slug}
        )
