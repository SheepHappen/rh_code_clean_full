from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.generic import UpdateView, TemplateView
from django.urls import reverse

from riskfactor.models import RiskDataSet, CountryRisk
from .forms import CountryRiskForm
from .mixins import StaffAccessMixin


class RiskFactorValueListView(LoginRequiredMixin, StaffAccessMixin, TemplateView):
    template_name = "risk_factor_value_list.html"

    def get_context_data(self, **kwargs):
        risks = [factor.name for factor in RiskDataSet.objects.all()]

        risks = list(set(risks))
        risks.sort()

        records = RiskDataSet.objects.all()
        has_scores = False
        for record in records:
            if record.active_version and record.active_version.countryrisk_set.all():
                has_scores = True
                break

        kwargs.update({
            "risks": risks,
            "has_scores": has_scores
        })
        return super().get_context_data(**kwargs)


def RiskFactorValueTable(request):
    filter_val = request.GET.get('filter_value')

    if filter_val and filter_val != 'All':
        records = RiskDataSet.objects.filter(name=filter_val)
    else:
        records = RiskDataSet.objects.all()

    data = []

    for record in records:
        if record and record.active_version:
            for item in record.active_version.countryrisk_set.all():
                country = item.country.name

                if country:
                    exposure = item.exposure

                    if exposure is None:
                        exposure = 'Null'

                    data.append({
                        'id': item.id,
                        'riskfacter': record.name,
                        'country': country,
                        'exposure': exposure,
                        'edit': "<a class='btn btn-primary' href={}>Edit<a/>".format(
                            reverse('risk_factor_values_detail', kwargs={'pk': item.id})
                        ),
                    })

    response = {
        'data': data,
        'recordsTotal': records.count(),
        'recordsFiltered': records.count(),
    }

    return JsonResponse(response)


class RiskFactorValueDetailView(LoginRequiredMixin, UpdateView):
    model = CountryRisk
    form_class = CountryRiskForm
    template_name = "risk_factor_value_detail.html"
    success_message = "Risk Factor Value updated successfully"
    success_url = '.'

    def get_object(self):
        return get_object_or_404(CountryRisk, id=self.kwargs['pk'])
