from users.models import User
from django.db import models
from django.dispatch import receiver

from allauth.account.signals import password_changed
from sorl.thumbnail import ImageField

from core.models import UuidPrimaryKeyModel
from company.models import Company


class UserProfile(UuidPrimaryKeyModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    job_title = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=64, blank=True, default="")
    avatar = ImageField(upload_to="user/avatars", blank=True, null=True, verbose_name="Headshot")
    company = models.ForeignKey(
        Company,
        null=True,
        blank=True,
        related_name='users',
        on_delete=models.CASCADE
    )
    hear_about_us = models.TextField(
        blank=True,
        null=True,
        verbose_name="How Did You Hear About Us?"
    )
    force_password_change = models.BooleanField(
        blank=True,
        default=False,
        verbose_name="Force password change?"
    )

    def __str__(self):
        return self.user.username


@receiver(password_changed)
def after_user_changed_password(request, **kwargs):
    UserProfile.objects.filter(
        user=kwargs['user']
    ).update(force_password_change=False)
