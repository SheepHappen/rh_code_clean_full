from datetime import date

import tablib

from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms.models import modelformset_factory
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import HttpResponse

from .forms import KpiForm
from company.models import CompanyAssessment
from .models import KeyPerformanceIndicator


class CompanyAssessmentKpiView(LoginRequiredMixin, View):
    template_name = "assessment_kpi.html"
    form_fields = ['aspect', 'is_kpi', 'detail', 'sdg_alignment', 'related_standard', 'status', 'commentary']

    def get(self, request, slug=None):
        assessment = get_object_or_404(
            CompanyAssessment,
            slug=slug,
            created_by__userprofile__company=self.request.user.userprofile.company
        )

        previous_url = request.META.get('HTTP_REFERER')
        kpi_list_url = reverse('company_kpi_list', kwargs={'slug': assessment.slug})

        if assessment.keyperformanceindicator_set.all() and previous_url and kpi_list_url not in previous_url:
            return redirect(
                reverse(
                    'company_kpi_list',
                    kwargs={'slug': assessment.slug}
                )
            )

        if assessment.keyperformanceindicator_set.all():
            extra = 0
        else:
            extra = 1

        kpi_forms = modelformset_factory(KeyPerformanceIndicator, form=KpiForm, fields=self.form_fields, extra=extra)
        kpi_forms = kpi_forms(queryset=KeyPerformanceIndicator.objects.filter(assessment=assessment))

        return render(request, self.template_name, {
            'kpi_forms': kpi_forms,
            'previous_url': previous_url,
            'assessment': assessment
        })

    def post(self, request, slug=None, *args, **kwargs):
        assessment = get_object_or_404(
            CompanyAssessment,
            slug=slug,
            created_by__userprofile__company=self.request.user.userprofile.company
        )

        kpi_forms = modelformset_factory(KeyPerformanceIndicator, fields=self.form_fields)
        formset = kpi_forms(request.POST)
        if formset.is_valid():
            for form in formset:
                instance = form.save(commit=False)
                instance.assessment = assessment
                instance.save()
                form.save_m2m()

        return redirect(
            reverse(
                'company_kpi_list',
                kwargs={'slug': assessment.slug}
            )
        )


class CompanyAssessmentKpiListView(LoginRequiredMixin, View):
    template_name = "assessment_kpi_list.html"

    def get(self, request, slug=None):
        assessment = get_object_or_404(
            CompanyAssessment,
            slug=slug,
            created_by__userprofile__company=self.request.user.userprofile.company
        )
        return render(request, self.template_name, {
            'assessment': assessment,
            'previous_url': request.META.get('HTTP_REFERER')
        })


def Download_kpi_csv(request, slug):
    assessment = get_object_or_404(CompanyAssessment, slug=slug)

    export_data = tablib.Dataset(
        headers=[
            'Aspect',
            'KPI',
            'Detail',
            'SDG alignment',
            'Related standard',
            'Status',
            'Commentary'
        ]
    )

    for kpi in assessment.keyperformanceindicator_set.all():
        if kpi.is_kpi:
            is_kpi = 'True'
        else:
            is_kpi = 'False'

        export_data.append([
            kpi.aspect.name,
            is_kpi,
            kpi.detail,
            kpi.sdg_alignment_list(),
            kpi.related_standards_list(),
            kpi.get_status_display(),
            kpi.commentary,
        ])

    filename = 'KPIs_{}.xlsx'.format(date.today())

    response = HttpResponse(export_data.export('customxlsx'), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="{}.xlsx"'.format(filename)

    return response
