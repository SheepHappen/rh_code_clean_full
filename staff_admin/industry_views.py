import tablib

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.management import call_command
from django.http import HttpResponseRedirect, JsonResponse, response
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import UpdateView, CreateView, TemplateView

from company.models import Industry
from company.forms import IndustryForm

from .mixins import StaffAccessMixin


class IndustryDetailView(LoginRequiredMixin, StaffAccessMixin, SuccessMessageMixin, UpdateView):
    model = Industry
    form_class = IndustryForm
    template_name = "industry_detail.html"
    success_message = "Industry updated successfully"
    success_url = reverse_lazy('industries_list')

    def get_object(self):
        return get_object_or_404(Industry, id=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if data['industry'].industryriskdataset_set.first():
            data['version'] = data['industry'].industryriskdataset_set.first().dataset_version
            data['current_data'] = data['version'].materialityrisk_set.all().order_by('risk_factor__name')
        try:
            tablib.Dataset().load(data['industry'].industryriskdataset_set.first().dataset_version.file_obj)
            data['file_obj'] = True
        except:
            pass
        return data


class IndustryListView(LoginRequiredMixin, StaffAccessMixin, TemplateView):
    template_name = "industry_list.html"

    def post(self, request):
        if "spreadsheet" in request.FILES:
            imported_data = tablib.Dataset().load(request.FILES['spreadsheet'])

            if imported_data.headers != ['Industry name', 'Description (optional)', 'Short description (optional)']:
                messages.add_message(request, messages.ERROR, "Incorrect file")
                return HttpResponseRedirect(reverse("industries_list"))

            for row in imported_data:
                industry, _ = Industry.objects.get_or_create(name=row[0],)

                industry.description = row[1]
                industry.short_description = row[2]
                industry.save()

            messages.add_message(request, messages.SUCCESS, "Imported Industries successfully")
        return HttpResponseRedirect(reverse("industries_list"))


def IndustryListTable(request):
    records = Industry.objects.all().distinct()

    data = []

    for record in records:
        data.append({
            'edit': "<a class='btn btn-primary' href={}>Edit<a/>".format(
                reverse('industry_detail', kwargs={'pk': record.id}),
            ),
            'text': record.name,
            'description': record.description,
            'short_description': record.short_description,
            'link': record.id,
            'sasbUpdate': "<a class='btn' href={} target='_blank'>Update sasb records<a/>".format(
                reverse('industry_sasb_table_update', kwargs={'pk': record.id}),
            ),
        })

    response = {
        'data': data,
        'recordsTotal': records.count(),
        'recordsFiltered': records.count(),
    }

    return JsonResponse(response)


class IndustryCreateView(LoginRequiredMixin, StaffAccessMixin, SuccessMessageMixin, CreateView):
    template_name = "industry_create.html"
    mmodel = Industry
    form_class = IndustryForm
    success_message = "industry created"

    def get_success_url(self):
        return reverse("industries_list")


def DeleteIndustry(request, pk):
    industry = get_object_or_404(Industry, id=pk)
    industry.delete()

    messages.add_message(request, messages.SUCCESS, "Successfully Deleted Industry")
    return HttpResponseRedirect(reverse("industries_list"))


def UpdateSasb(request, pk):
    industry = get_object_or_404(Industry, id=pk)
    response = call_command('import_sasb_data', "--industry_name", industry.name)
    if response == '500':
        messages.add_message(request, messages.ERROR, "An error has occured, please try later, if it happens again please contact the admin")
    if response == '200':
        messages.add_message(request, messages.SUCCESS, "Sasb table updated")
    return HttpResponseRedirect(reverse("industries_list"))


def UpdateAllSasb(request):
    response = call_command('import_sasb_data', "--update_all", True)
    if response == '500':
        messages.add_message(request, messages.ERROR, "An error has occured, please try later, if it happens again please contact the admin")
    if response == '200':
        messages.add_message(request, messages.SUCCESS, "Sasb table updated")
    return HttpResponseRedirect(reverse("industries_list"))


def RecreateAllSasb(request):
    response = call_command('import_sasb_data')
    if response == '500':
        messages.add_message(request, messages.ERROR, "An error has occured, please try later, if it happens again please contact the admin")
    if response == '200':
        messages.add_message(request, messages.SUCCESS, "Sasb table updated")
    return HttpResponseRedirect(reverse("industries_list"))