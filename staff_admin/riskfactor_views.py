import tablib

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import UpdateView, CreateView, TemplateView

from riskfactor.models import RiskDataSet, RiskFactorCategory
from riskfactor.forms import RiskDataSetForm
from .mixins import StaffAccessMixin


class RiskFactorCreateView(LoginRequiredMixin, StaffAccessMixin, SuccessMessageMixin, CreateView):
    template_name = "risk_factor_create.html"
    model = RiskDataSet
    form_class = RiskDataSetForm
    success_message = "Risk Factor created"

    def get_success_url(self):
        return reverse("riskfactors_list")


class RiskFactorListView(LoginRequiredMixin, StaffAccessMixin, TemplateView):
    template_name = "risk_factor_list.html"

    def get_context_data(self, **kwargs):
        categories = [category.name for category in RiskFactorCategory.objects.all()]
        categories = list(categories)
        categories.sort()

        kwargs.update({
            "categories": categories
        })
        return super().get_context_data(**kwargs)


class RiskFactorDetailView(LoginRequiredMixin, StaffAccessMixin, SuccessMessageMixin, UpdateView):
    model = RiskDataSet
    form_class = RiskDataSetForm
    template_name = "risk_factor_detail.html"
    success_message = "Risk Factor updated successfully"
    success_url = reverse_lazy('riskfactors_list')

    def get_initial(self):
        if self.object:
            return {'update_status': self.object.calculate_update_status()}

    def get_object(self):
        return get_object_or_404(RiskDataSet, id=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if data['riskdataset'].active_version:
            data['version'] = data['riskdataset'].active_version
            data['current_data'] = data['version'].countryrisk_set.all().order_by('country__name')

        try:
            tablib.Dataset().load(data['riskdataset'].active_version.file_obj)
            data['file_obj'] = True
        except:
            pass

        return data


def RiskFactorListDataTable(request):
    category = request.GET.get('category_value')

    if category and category != 'All':
        records = RiskDataSet.objects.filter(category__name=category).distinct()
    else:
        records = RiskDataSet.objects.all().distinct()

    data = []

    for record in records:
        data.append({
            'edit': "<a class='btn btn-primary' href={}>Edit<a/>".format(
                reverse('risk_factor_detail', kwargs={'pk': record.id}),
            ),
            'name': record.name,
            'category': record.category.name,
            'recommendation': record.recommendation,
            'link': record.id
        })

    response = {
        'data': data,
        'recordsTotal': records.count(),
        'recordsFiltered': records.count(),
    }

    return JsonResponse(response)


def DeleteRiskFactor(request, pk):
    risk = get_object_or_404(RiskDataSet, id=pk)
    risk.delete()

    messages.add_message(request, messages.SUCCESS, "Successfully Deleted Risk Factor")
    return HttpResponseRedirect(reverse("riskfactors_list"))
