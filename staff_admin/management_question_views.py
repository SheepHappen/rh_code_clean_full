import tablib

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import UpdateView, CreateView, TemplateView

from core.models import ManagementQuestion
from core.forms import ManagementQuestionForm
from riskfactor.models import RiskDataSet
from .mixins import StaffAccessMixin


class ManagementQuestionDetailView(LoginRequiredMixin, StaffAccessMixin, SuccessMessageMixin, UpdateView):
    model = ManagementQuestion
    form_class = ManagementQuestionForm
    template_name = "management_question_detail.html"
    success_message = "Management question updated successfully"
    success_url = reverse_lazy('management_questions_list')

    def get_object(self):
        return get_object_or_404(ManagementQuestion.objects.all().select_related('company'), id=self.kwargs['pk'])


class ManagementQuestionCreateView(LoginRequiredMixin, StaffAccessMixin, SuccessMessageMixin, CreateView):
    template_name = "management_question_create.html"
    model = ManagementQuestion
    form_class = ManagementQuestionForm
    success_message = "Management question created"

    def get_success_url(self):
        return reverse("management_questions_list")


class ManagementQuestionsListView(LoginRequiredMixin, StaffAccessMixin, TemplateView):
    template_name = "management_questions_list.html"

    def get_context_data(self, **kwargs):
        kwargs.update({
            "risks": RiskDataSet.objects.all().order_by('name').values_list('name', flat=True)
        })
        return super().get_context_data(**kwargs)

    def post(self, request):
        if "spreadsheet" in request.FILES:
            imported_data = tablib.Dataset().load(request.FILES['spreadsheet'])

            if imported_data.headers != ['Question', 'Category', 'Risk Factor']:
                messages.add_message(request, messages.ERROR, "Incorrect file")
                return HttpResponseRedirect(reverse("management_questions_list"))

            for row in imported_data:
                if row[1].lower() == 'e':
                    category = 'ENVIRONMENT'
                elif row[1].lower() == 's':
                    category = 'SOCIAL'
                else:
                    category = 'GOVERNANCE'

                management_question, _ = ManagementQuestion.objects.get_or_create(
                    category=category,
                    text=row[0],
                )

                for risk in row[2].split(','):
                    risk = RiskDataSet.objects.filter(name=risk.strip())
                    if risk:
                        management_question.riskfactors.add(risk.first())

                management_question.save()

            messages.add_message(request, messages.SUCCESS, "Imported Management Questions successfully")
        return HttpResponseRedirect(reverse("management_questions_list"))


def ManagementQuestionTable(request):
    filter_val = request.GET.get('filter_value')

    if filter_val and filter_val != 'All':
        records = ManagementQuestion.objects.filter(riskfactors__name=filter_val).distinct()
    else:
        records = ManagementQuestion.objects.all().distinct()

    data = []

    for record in records:
        data.append({
            'edit': "<a class='btn btn-primary' href={}>Edit<a/>".format(
                reverse('management_question_detail', kwargs={'pk': record.id}),
            ),
            'text': record.text,
            'category': record.get_category_display(),
            'riskfactor': list(record.riskfactors.values_list('name', flat=True)),
            'company': record.company.name if record.company else '-',
            'link': record.id
        })

    response = {
        'data': data,
        'recordsTotal': records.count(),
        'recordsFiltered': records.count(),
    }

    return JsonResponse(response)


def DeleteManagementQuestion(request, pk):
    management_question = get_object_or_404(ManagementQuestion, id=pk)
    management_question.delete()

    messages.add_message(request, messages.SUCCESS, "Successfully Deleted ManagementQuestion")
    return HttpResponseRedirect(reverse("management_questions_list"))
