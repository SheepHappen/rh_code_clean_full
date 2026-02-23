from core.models import UuidPrimaryKeyModel

from django.contrib.auth.models import AbstractUser
from django_extensions.db.fields import AutoSlugField
from django.urls import reverse


class User(AbstractUser, UuidPrimaryKeyModel):
    slug = AutoSlugField(max_length=255, editable=False, populate_from=["username"])

    def get_admin_url(self):
        return reverse('admin:%s_%s_change' % (self._meta.app_label, self._meta.model_name), args=[self.id])
