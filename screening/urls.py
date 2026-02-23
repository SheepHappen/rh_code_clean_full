from django.urls import path

from . import views

urlpatterns = [
    path(
        '',
        views.ScreeningView.as_view(),
        name='screening-tool'
    ),
    path(
        'industry-comparison-table/',
        views.Industry_comparison_table,
        name='industry_comparison_table'
    ),
    path(
        'geo-comparison-table/',
        views.Geographic_comparison_table,
        name='geographic_comparison_table'
    ),
    path(
        'data_csv/',
        views.dataCsv.as_view(),
        name='screening_download'
    ),
]
