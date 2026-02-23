from django.urls import path

from . import views

urlpatterns = [
    path(
        '<slug:slug>/',
        views.CompanyAssessmentKpiView.as_view(),
        name='company_kpi'
    ),
    path(
        'kpi_list/<slug:slug>/',
        views.CompanyAssessmentKpiListView.as_view(),
        name='company_kpi_list'
    ),
    path(
        'kpi_csv/<slug:slug>/',
        views.Download_kpi_csv,
        name='kpi_csv_download'
    ),
]
