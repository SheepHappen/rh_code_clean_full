from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from allauth.account.views import LoginView

from accounts.views import CustomPasswordChangeView
from core.forms import AxesLoginForm

urlpatterns = [
    path('landmark-backend-admin/', admin.site.urls),
    path(
        'accounts/password/change/',
        CustomPasswordChangeView.as_view(),
        name='account_change_password'
    ),
    path("", LoginView.as_view(form_class=AxesLoginForm), name="home"),
    path("accounts/", include("allauth.urls")),
    path('staff-admin/', include('staff_admin.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('portfolio/', include('portfolio.urls')),
    path('screening/', include('screening.urls')),
    path('company/', include('company.urls')),
    path('kpi/', include('kpi.urls')),
    path('accounts/', include('accounts.urls')),
    path('geography/', include('geo.urls')),
    path('report/', include('report.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    # import debug_toolbar
    # urlpatterns += [
    #     path('__debug__/', include(debug_toolbar.urls)),
    # ]
