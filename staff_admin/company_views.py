from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import UpdateView, TemplateView

from core.models import Permission
from company.models import Company
from company.forms import CompanyForm

from .mixins import StaffAccessMixin


class CompanyListView(LoginRequiredMixin, StaffAccessMixin, TemplateView):
    template_name = "company_list.html"


def CompanyTable(request):
    records = Company.objects.all().distinct()

    data = []

    for record in records:
        data.append({
            'edit': "<a class='btn btn-primary' href={}>Edit<a/>".format(
                reverse('company_detail', kwargs={'pk': record.id}),
            ),
            'text': record.name,
            'link': record.id
        })

    response = {
        'data': data,
        'recordsTotal': records.count(),
        'recordsFiltered': records.count(),
    }

    return JsonResponse(response)


class CompanyDetailView(LoginRequiredMixin, StaffAccessMixin, SuccessMessageMixin, UpdateView):
    model = Company
    form_class = CompanyForm
    template_name = "company_detail.html"
    success_message = "Company updated successfully"
    success_url = reverse_lazy('company_list')

    def get_object(self):
        return get_object_or_404(Company, id=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        permissions = Permission.objects.all()
        company = self.object

        if permissions:
            data['permissions'] = []
            for permission in permissions:
                has_permission = False
                if permission in company.permissions.all():
                    has_permission = True
                data['permissions'].append({
                    'name': permission.name,
                    'id': permission.id,
                    'access': has_permission
                })

        return data


def TogglePermission(request):
    company_id = request.GET.get('company_id')
    company = Company.objects.get(id=company_id)
    permission_id = request.GET.get('permission_id')
    permission = Permission.objects.get(id=permission_id)
    action = request.GET.get('action')

    if action == 'grant':
        company.permissions.add(permission)
    if action == 'revoke':
        company.permissions.remove(permission)

    company.save()

    return JsonResponse({})
