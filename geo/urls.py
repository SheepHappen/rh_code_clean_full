from django.urls import path

from . import views

urlpatterns = [
    path(
        'assessment/',
        views.GeoAssessmentView.as_view(),
        name='geo_assessment'
    ),
    path(
        'assessment_data/',
        views.assessmentDataDownload.as_view(),
        name='geo_assessment_data_download'
    ),
    path(
        'assessment_data_all/',
        views.assessmentDataDownloadAll.as_view(),
        name='geo_assessment_all_data_download'
    ),
]
