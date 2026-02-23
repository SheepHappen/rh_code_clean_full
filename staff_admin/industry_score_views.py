import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import UpdateView, TemplateView

from company.models import Industry
from riskfactor.models import RiskDataSet, IndustryRiskDataSet, MaterialityRisk

from .forms import MaterialityRiskForm
from .mixins import StaffAccessMixin


class IndustryRiskValueListView(LoginRequiredMixin, StaffAccessMixin, TemplateView):
    template_name = "industry_risk_factor_value_list.html"

    def get_context_data(self, **kwargs):
        risks = [factor.name for factor in RiskDataSet.objects.all()]

        risks = list(set(risks))
        risks.sort()

        records = IndustryRiskDataSet.objects.all()
        has_scores = False
        for record in records:
            if record.dataset_version:
                has_scores = True
                break

        kwargs.update({
            "risks": risks,
            "has_scores": has_scores,
            "industries": list(Industry.objects.values_list('name', flat=True))
        })
        return super().get_context_data(**kwargs)


def IndustryRiskFactorValueTable(request):
    filter_val = request.GET.get('filter_value')
    industry_filter = request.GET.get('industry_filter')

    new_industry_data = request.GET.get('industry_uploads')

    versions = IndustryRiskDataSet.objects.filter(dataset_version__isnull=False).values_list('dataset_version_id', flat=True)

    if filter_val == 'All':
        filter_val = None
    if industry_filter == 'All':
        industry_filter = None

    data = []
    records = MaterialityRisk.objects.filter(dataset_version_id__in=versions)

    if new_industry_data:
        records = records.filter(
            industry__name__in=json.loads(new_industry_data)
        )
    else:
        if filter_val and industry_filter:
            records = records.filter(
                risk_factor__name=filter_val,
                industry__name=industry_filter
            )
        elif filter_val:
            records = records.filter(
                risk_factor__name=filter_val
            )
        elif industry_filter:
            records = records.filter(
                industry__name=industry_filter
            )

    for record in records:
        data.append({
            'edit': "<a class='btn btn-primary' href={}>Edit<a/>".format(
                reverse('industry_risk_factor_values_detail', kwargs={'pk': record.id})
            ),
            'industry': record.industry.name,
            'risk_factor': record.risk_factor.name,
            'materiality': record.materiality if record.materiality else 'Null',
            'source': record.source.name,
            'link': record.id
        })

    response = {
        'data': data,
        'recordsTotal': records.count(),
        'recordsFiltered': records.count(),
    }

    return JsonResponse(response)


class IndustryRiskFactorValueDetailView(LoginRequiredMixin, StaffAccessMixin, UpdateView):
    model = MaterialityRisk
    form_class = MaterialityRiskForm
    template_name = "materiality_detail.html"
    success_message = "MaterialityRisk updated successfully"
    success_url = '.'

    def get_object(self):
        return get_object_or_404(MaterialityRisk, id=self.kwargs['pk'])
