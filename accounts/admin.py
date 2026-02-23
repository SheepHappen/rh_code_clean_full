from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from users.models import User

from .import models


class ProfileInline(admin.StackedInline):
    model = models.UserProfile
    can_delete = False
    extra = 0
    verbose_name_plural = 'Profile'
    fk_name = 'user'
    max_num = 1


class CustomUserAdmin(UserAdmin):
    inlines = (ProfileInline, )

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super(CustomUserAdmin, self).get_inline_instances(request, obj)


admin.site.register(User, CustomUserAdmin)
admin.site.register(models.UserProfile)
