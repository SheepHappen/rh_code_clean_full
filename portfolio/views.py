import tablib
import re

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Count, Case, When, Q
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import View

from core.models import Threshold, DocumentQuestion
from company.models import CompanyAssessment
from company.calc import calculate_rev_counter_score, calculate_top_5_impact_score
from company.views import get_document_question_answer
from riskfactor.models import RiskDataSet, CountryRisk


class PortfolioView(LoginRequiredMixin, View):
    template_name = "portfolio.html"

    def get(self, request, pk=None):
        if CompanyAssessment.objects.filter(
            created_by__userprofile__company__name=request.user.userprofile.company.name
        ).exists():
            has_assessments = True
            companies = CompanyAssessment.objects.filter(
                created_by__userprofile__company__name=request.user.userprofile.company.name
            ).select_related('parent').select_related('custom_risk_score').select_related('created_by').select_related('company_fund').values_list(
                'company_name', 'company_name').order_by('company_name'
            ).distinct()
            funds = request.user.userprofile.company.companyfund_set.filter(enabled=True)
            document_questions = DocumentQuestion.objects.filter(pdf_display_order__isnull=False).order_by(
                'pdf_display_order'
            ).select_related('company').select_related('trigger_question').values_list('pdf_display_name', flat=True)

            risk_factors = RiskDataSet.objects.all().select_related('active_version').select_related('category').values_list('name', flat=True)
        else:
            initial_card_text = {
                'heading': "You haven’t added any companies to your portfolio",
                'text': ' Add companies to the funds in your portfolio from the dashboard assessment manager or when running a new assessment',
                'button_text': 'New assessment'
            }

        return render(request, self.template_name, locals())


def calculate_risk_factor_score(country_ids, version_list):
    risks_scores = CountryRisk.objects.filter(
        country_id__in=country_ids,
        version_id__in=version_list,
        exposure__isnull=False
    ).select_related('version').select_related('country').values_list('exposure', flat=True)

    exposure = sum(risks_scores)
    total_risks = len(country_ids)

    if exposure > 0 and total_risks > 0:
        score = exposure / total_risks
        return round(score, 2)

    return 'N/A'


def cleanhtml(raw_html):
    cleanr = re.compile('<.*?>')
    return re.sub(cleanr, '', raw_html)


def get_risk_name(risk):
    if isinstance(risk, dict):
        return risk['name']
    return risk.name


def get_version(risk):
    return risk.active_version


def get_country_id(country):
    return int(country.id)


def PortfolioTable(request):
    data = []
    export = request.GET.get('export', False)
    if export:
        export_data = tablib.Dataset(
            headers=[
                'Company', 'Fund', 'Risk factor', 'Document(s)',
                'ESG score', 'Inherent risk score', 'Risk factor score',
                'Document status', 'Possible total', 'KPIs', 'Actions'
            ]
        )
        document_select_filter = request.POST.get('document_select_filter', None)
        risk_select_filter = request.POST.get('risk_select_filter', None)
        company_select_filter = request.POST.get('company_select_filter', None)
        fund_select_filter = request.POST.get('fund_select_filter', None)
    else:
        document_select_filter = request.GET.get('document_select_filter', None)
        risk_select_filter = request.GET.get('risk_select_filter', None)
        company_select_filter = request.GET.get('company_select_filter', None)
        fund_select_filter = request.GET.get('fund_select_filter', None)

    if document_select_filter and document_select_filter != 'all_documents':
        document_questions = DocumentQuestion.objects.get(pdf_display_name=document_select_filter)
    else:
        document_questions = DocumentQuestion.objects.filter(pdf_display_order__isnull=False).order_by('pdf_display_order')

    records = CompanyAssessment.objects.filter(
        created_by__userprofile__company__name=request.user.userprofile.company.name
    ).select_related(
        'created_by'
    ).select_related(
        'company_fund'
    ).select_related('custom_risk_score').order_by('company_name')

    record_count = records.count()

    if company_select_filter and company_select_filter != 'all_companies':
        records = records.filter(company_name=company_select_filter)

    if fund_select_filter and fund_select_filter != 'all_funds':
        records = records.filter(company_fund__slug=fund_select_filter)

    if risk_select_filter and risk_select_filter != 'all_risks':
        records = records.filter(material_risks__name=risk_select_filter)

    if export:
        paginated_records = records
    else:
        paginator = Paginator(records, request.GET.get('page_length', 20))
        page = request.GET.get('page')
        paginated_records = paginator.get_page(page)

    for record in paginated_records:
        funds = record.company_fund.name if record.company_fund else 'N/A'
        industry_data = record.industries.all().values_list('slug', flat=True)
        country_list = list(map(get_country_id, record.countries.all()))

        risks = record.material_risks.all().only('id', 'name', 'active_version')
        all_risks, overall_inherent_risk_score = calculate_top_5_impact_score(risks, industry_data, country_list, True)

        threshold_text = Threshold.objects.filter(
            lower_bound__lte=overall_inherent_risk_score,
            upper_bound__gte=overall_inherent_risk_score
        ).values_list('text', flat=True).first()

        has_document = 0
        if document_select_filter and document_select_filter != 'all_documents':
            answer = get_document_question_answer(record, document_questions)
            document_status = 'No Evidence'
            if answer and answer.answer:
                if answer.answer == 'Y':
                    document_status = 'Yes'
                    has_document += 1
                elif answer.answer == 'No':
                    document_status = 'No'
        else:
            for question in document_questions:
                answer = get_document_question_answer(record, question)
                if answer and answer.answer:
                    if answer.answer == 'Y':
                        has_document += 1
            document_status = '{}/{}'.format(has_document, len(document_questions))

        esg_score = calculate_rev_counter_score(record)
        if esg_score != 0:
            esg_score = '{}%'.format(esg_score)

        risk_factor_score = 'N/A'
        risk_list = list(map(get_risk_name, risks))

        if risk_select_filter and risk_select_filter != 'all_risks':
            active_version_list = list(map(get_version, risks))
            risk_factor_score = calculate_risk_factor_score(country_list, active_version_list)

        kpi_dict = record.keyperformanceindicator_set.aggregate(
            total_kpi=Count(Case(When(is_kpi=True, then=1))),
            total_action=Count(Case(When(is_kpi=False, then=1))),
            action_done=Count('pk', filter=Q(is_kpi=False, status='A') | Q(is_kpi=False, status='N')),
            kpi_done=Count('pk', filter=Q(is_kpi=True, status='A') | Q(is_kpi=True, status='N'))
        )

        if export:
            export_data.append([
                record.company_name,
                funds,
                ', '.join(risk_list),
                ', '.join(document_questions.values_list('pdf_display_name', flat=True)) if not hasattr(document_questions, 'pdf_display_name') else document_questions.pdf_display_name,
                esg_score,
                overall_inherent_risk_score,
                risk_factor_score,
                has_document,
                document_questions.count() if not hasattr(document_questions, 'pdf_display_name') else 'N/A',
                "{}/{}".format(kpi_dict['kpi_done'], kpi_dict['total_kpi']),
                "{}/{}".format(kpi_dict['action_done'], kpi_dict['total_action']),
            ])
        else:
            append = False
            if risk_select_filter and risk_select_filter != 'all_risks':
                if risk_factor_score != 'N/A':
                    append = True
            else:
                append = True

            if append:
                data.append({
                    'company': "<a style='margin-left:0.625rem;' href={}>{}<a/>".format(
                        reverse('company_assessment_key_detail', kwargs={'slug': record.slug}),
                        cleanhtml(record.company_name)
                    ),
                    'fund': funds,
                    'esg_score': esg_score,
                    'inherent_risk': threshold_text,
                    'risk_factor': risk_factor_score,
                    'document_status': document_status,
                    'kpi': "{}/{}".format(kpi_dict['kpi_done'], kpi_dict['total_kpi']),
                    'action': "{}/{}".format(kpi_dict['action_done'], kpi_dict['total_action']),
                })

    if export:
        response = HttpResponse(export_data.export('customxlsx'), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="porfolio_manager.xlsx"'

        return response
    else:
        return JsonResponse({
            'data': data,
            'recordsTotal': record_count,
            'recordsFiltered': 20,
            'page_num': paginated_records.number,
            'total_pages': paginated_records.paginator.num_pages
        })
