from django.http import HttpResponseRedirect
from django.urls import reverse


class StaffAccessMixin(object):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser and not request.user.is_staff:
            return HttpResponseRedirect(reverse('dashboard'))
        else:
            return super().dispatch(request, *args, **kwargs)
