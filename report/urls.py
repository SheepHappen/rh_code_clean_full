from django.urls import path

from . import views

urlpatterns = [
    path(
        'pdf/<slug:slug>/',
        views.ReportView.as_view(),
        name='report_view'
    ),
]
