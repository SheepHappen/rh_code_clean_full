from django.urls import path

from . import views

urlpatterns = [
    path(
        '',
        views.DashboardView.as_view(),
        name='dashboard'
    ),
    path(
        'add-fund-to-assessment',
        views.add_fund_to_assessment,
        name='add_fund_to_assessment'
    ),
]
