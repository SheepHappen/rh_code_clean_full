import tablib

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import UpdateView, CreateView, TemplateView

from core.models import DocumentQuestion
from core.forms import DocumentQuestionForm
from .mixins import StaffAccessMixin


class DocumentQuestionDetailView(LoginRequiredMixin, StaffAccessMixin, SuccessMessageMixin, UpdateView):
    model = DocumentQuestion
    form_class = DocumentQuestionForm
    template_name = "document_question_detail.html"
    success_message = "Document question updated successfully"
    success_url = reverse_lazy('document_questions_list')

    def get_object(self):
        return get_object_or_404(DocumentQuestion, id=self.kwargs['pk'])


class DocumentQuestionCreateView(LoginRequiredMixin, StaffAccessMixin, SuccessMessageMixin, CreateView):
    template_name = "document_question_create.html"
    model = DocumentQuestion
    form_class = DocumentQuestionForm
    success_message = "Document question created"

    def get_success_url(self):
        return reverse("document_questions_list")


def buildTriggerQuestions(parentQuestion, records):
    counter = 1
    for text, score in zip(records[0::2], records[1::2]):
        if text and score:
            trigger_question, _ = DocumentQuestion.objects.get_or_create(
                category=parentQuestion.category,
                text=text,
            )
            trigger_question.display_order = counter
            trigger_question.trigger_question = parentQuestion
            counter += 1

            if score.lower() == 'yes':
                trigger_question.yes_score = 1
                trigger_question.no_score = 0
            if score.lower() == 'no':
                trigger_question.yes_score = 0
                trigger_question.no_score = 1

            trigger_question.save()


class DocumentQuestionsListView(LoginRequiredMixin, StaffAccessMixin, TemplateView):
    template_name = "document_questions_list.html"

    def post(self, request):
        if "spreadsheet" in request.FILES:
            imported_data = tablib.Dataset().load(request.FILES['spreadsheet'])

            if 'Document checklist question' not in imported_data.headers:
                messages.add_message(request, messages.ERROR, "Incorrect file")
                return HttpResponseRedirect(reverse("document_questions_list"))
            for row in imported_data:
                category = row[1].lower()
                if category[0] == 'e':
                    category = 'ENVIRONMENT'
                elif category[0] == 's':
                    category = 'SOCIAL'
                else:
                    category = 'GOVERNANCE'

                question, _ = DocumentQuestion.objects.get_or_create(
                    category=category,
                    text=row[2],
                )
                question.display_order = int(row[0])
                if row[3].lower() == 'yes':
                    question.yes_score = 1
                    question.no_score = 0
                    if row[4:]:
                        buildTriggerQuestions(question, row[4:])
                elif row[3].lower() == 'no':
                    question.yes_score = 0
                    question.no_score = 1
                elif row[3].lower() == 'null':
                    question.yes_score = None
                    question.no_score = None
                    if row[4:]:
                        question.is_answerable = False
                        buildTriggerQuestions(question, row[4:])
                question.save()

            messages.add_message(request, messages.SUCCESS, "Imported ManagementQuestions successfully")
        return HttpResponseRedirect(reverse("document_questions_list"))


def DocumentQuestionTable(request):
    records = DocumentQuestion.objects.all().distinct()

    data = []

    for record in records:
        data.append({
            'edit': "<a class='btn btn-primary' href={}>Edit<a/>".format(
                reverse('document_question_detail', kwargs={'pk': record.id})
            ),
            'text': record.text,
            'category': record.get_category_display(),
            'company': record.company.name if record.company else '-',
            'link': record.id
        })

    response = {
        'data': data,
        'recordsTotal': records.count(),
        'recordsFiltered': records.count(),
    }

    return JsonResponse(response)


def DeleteDocumentQuestion(request, pk):
    question = get_object_or_404(DocumentQuestion, id=pk)
    question.delete()

    messages.add_message(request, messages.SUCCESS, "Successfully Deleted Document Question")
    return HttpResponseRedirect(reverse("document_questions_list"))
