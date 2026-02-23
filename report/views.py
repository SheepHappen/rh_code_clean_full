from collections import OrderedDict

from django_weasyprint import WeasyTemplateView

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models.functions import Lower
from django.shortcuts import get_object_or_404
from country.models import Country, SanctionedCountry

from .models import pdfContactDetail
from core.models import DocumentQuestion, Threshold
from core.utils import get_score_colour
from company.models import CompanyAssessment, AssessmentIssueRecommendations, DocumentQuestionAnswerSet
from company.calc import calculate_rev_counter_score, calculate_top_5_impact_score, calculate_top_5_at_risk_countrys, calculate_document_question_complete
from company.views import get_risk_by_source, get_document_question_answer, get_and_split_document_questions, get_key_document_answer_count
from riskfactor.models import RiskDataSet, CountryRisk, IndustryRiskDataSet, RiskFactorCategory

import plotly.express as px
import base64


def get_environmental_questions(questions, category, assessment):
    questions = [question for question in questions if question.category == category]
    questions_list = []
    for question in questions:
        if not hasattr(question, 'answer'):
            answer = assessment.get_mananagement_question_answer(question)
            if answer:
                question.answer = answer.answer
                question.insufficient = answer.insufficient
                question.priority = answer.priority
                questions_list.append(question)
        if hasattr(question, 'hightlight') and question.hightlight or question.answer and question not in questions_list:
            questions_list.append(question)

    return questions_list, len(questions_list)


def get_recommendations(impacts, assessment):
    risk_list = []
    for impact in impacts:
        issue = AssessmentIssueRecommendations.objects.filter(
            assessment=assessment,
            issue=impact.name
        ).select_related('assessment')
        if issue:
            risk_list.append({
                'risk': issue[0].issue,
                'text': issue[0].recommendation
            })
        else:
            if hasattr(impact, 'obj_id'):
                org_risk = RiskDataSet.objects.get(id=impact.obj_id)
            else:
                org_risk = RiskDataSet.objects.get(id=impact.id)

            risk_list.append({
                'risk': org_risk.name,
                'text': org_risk.recommendation
            })

    return risk_list


def get_country_preparedness(countries):
    country_preparedness = {}
    for country in countries:
        if country.score > 0 and country.score < 2.5:
            dict_key = 'most_prepared'
        elif country.score > 0.5 and country.score < 5:
            dict_key = 'more_prepared'
        elif country.score > 5:
            dict_key = 'least_prepared'

        if dict_key in country_preparedness.keys():
            country_preparedness[dict_key].extend([country.name])
        else:
            country_preparedness[dict_key] = [country.name]

    return custom_sort_dict(country_preparedness, ['most_prepared', 'more_prepared', 'least_prepared'])


def country_graph(assessment):
    sample_data = {}
    existing = [record.iso2 for record in assessment.countries.all()]
    countries = Country.objects.all()

    for country in countries:
        if country.iso2 in existing:
            sample_data[country.iso3] = 1
        else:
            sample_data[country.iso3] = 0

    if existing:
        colours = ['#7B7C6A', '#F58520']
    else:
        colours = ['#7B7C6A', '#7B7C6A']

    fig = px.choropleth(
        locations=list(sample_data.keys()),
        color=list(sample_data.values()),
        color_continuous_scale=colours,
    )

    fig.update_layout(
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        showlegend=False,
        coloraxis_showscale=False,
        geo=dict(
            showframe=False,
            lataxis_range=[-60, 100],
        ),
    )
    fig.update_traces(marker_line_color='white')

    img_bytes = fig.to_image(format="png", height=275, width=550, engine="kaleido")

    return f"data:image/png;base64,{str(base64.b64encode(img_bytes))[2:-1]}"


def custom_sort_dict(dict1, key_order):
    dict1 = {k.lower(): v for k, v in dict1.items()}
    items = [dict1[k] if k in dict1.keys() else 0 for k in key_order]
    sorted_dict = OrderedDict()

    for i in range(len(key_order)):
        if isinstance(items[i], list):
            sorted_dict[key_order[i]] = ", ".join(items[i])
        else:
            sorted_dict[key_order[i]] = 'Not identified'

    return sorted_dict


def get_risks_for_top_5_countries(records, selected_countries):
    risk_list = {}
    keys = Threshold.objects.all().order_by('-lower_bound').values_list(Lower('text'), flat=True)

    for country in selected_countries:
        for record in records.exclude(active_version__isnull=True):
            item = record.active_version.countryrisk_set.filter(country__id=country.obj_id).exclude(exposure__isnull=True).first()
            if item:
                threshold_text = Threshold.objects.filter(lower_bound__lte=item.exposure, upper_bound__gte=item.exposure)
                if threshold_text:
                    obj = [{
                        'score': threshold_text.first().text,
                        'risk': record.name,
                    }]
                    if country.name in risk_list.keys():
                        risk_list[country.name].extend(obj)
                    else:
                        risk_list[country.name] = [country.score] + obj
    gouped_list = []
    for key, value in risk_list.items():
        risks = {}
        for record in value[1:]:
            dict_key = record['score']
            if record['score'] in risks.keys():
                risks[dict_key].extend([record['risk']])
            else:
                risks[dict_key] = [record['risk']]

        gouped_list.append(
            {
                'country': key,
                'overall_score': value[0],
                'risks': custom_sort_dict(risks, keys),
                'colour': get_score_colour(value[0])
            }
        )

    return gouped_list


def sort_matrix_data(records):
    categories = RiskFactorCategory.objects.filter(sort_order__isnull=False).order_by('sort_order').values('name', 'sort_order')
    sort_order = {}
    for category in categories:
        sort_order[category['name']] = category['sort_order']

    headers = [{} for i in records]

    for count, record in enumerate(records):
        record.sort(key=lambda x: sort_order[x["category"]])
        industry = []
        country = []
        environmental_aside = int((len([item['category'] for item in record if item['category'] == 'Environmental' ]) / 2))
        social_aside = int((len([item['category'] for item in record if item['category'] == 'Social' ]))) + environmental_aside - 1
        governance_aside = int((len([item['category'] for item in record if item['category'] == 'Governance' ]))) + social_aside + 1

        for child_count, item in enumerate(record):
            industry = [item['name'] for item in item['risk_matrix']['industry']]
            country = [item['name'] for item in item['risk_matrix']['country']]
            if item['category'] == 'Environmental' and child_count == environmental_aside:
                item['side_count'] = 'Environmental'
            elif item['category'] == 'Social' and child_count == social_aside:
                item['side_count'] = 'Social'
            elif item['category'] == 'Governance' and child_count == governance_aside:
                item['side_count'] = 'Governance'

        headers[count]['industry_headers'] = industry
        headers[count]['country_headers'] = country

    return records, headers


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def get_risk_matrix(risks, countries, industries_list):
    countries = Country.objects.filter(id__in=countries).order_by('name')
    industries = IndustryRiskDataSet.objects.filter(industry__slug__in=industries_list).order_by('industry__name')

    max_columns = 14
    max_city_columns = max_columns - len(industries)
    countries = list(chunks(countries, max_city_columns))

    table_data = [[] for i in countries]
    for risk in risks:
        industries_table_data = []
        """
        For each risk get the industry score
        """
        for industry in industries:
            if industry.dataset_version:
                score = 'N/A'
                threshold = 'matrix-na'
                if industry.industry.slug in industries_list:
                    industry_risk = industry.dataset_version.materialityrisk_set.filter(risk_factor__id=risk.id).exclude(
                        materiality__isnull=True
                    ).first()
                    if industry_risk:
                        score = industry_risk.materiality
                        threshold = get_score_colour(score)

                industries_table_data.append({
                    'name': industry.industry.name,
                    'score': score,
                    'threshold': threshold
                })

        """
        For each risk get the country score
        """
        for count, country_items in enumerate(countries):
            country_data = []
            for country in country_items:
                score = 'N/A'
                threshold = 'matrix-na'
                if risk.active_version:
                    country_risk = CountryRisk.objects.filter(
                        country=country,
                        version__id=risk.active_version.id
                    ).exclude(
                        exposure__isnull=True
                    ).first()
                    if country_risk and country_risk.exposure:
                        score = country_risk.exposure
                        threshold = get_score_colour(score)

                country_data.append({
                    'name': country.name,
                    'score': score,
                    'threshold': threshold
                })

            table_data[count].append({
                'category': risk.category.name,
                'risk': risk.name,
                'risk_matrix': {
                    'industry': industries_table_data,
                    'country': country_data
                }
            })

    return sort_matrix_data(table_data)


class ReportView(LoginRequiredMixin, WeasyTemplateView):
    template_name = "report_template.html"
    pdf_stylesheets = [
        settings.STATIC_ROOT + '/css/bootstrap.min.css',
        settings.STATIC_ROOT + '/css/report.css',
    ]

    def filter_answered_or_required_questions(self, question):
        if question['is_required'] or question['answered']:
            return question

    def map_impact_slug(self, impact):
        return impact.slug

    def get_threshold_colour_and_text(self, score):
        if self.assessment.custom_risk_score:
            return self.assessment.custom_risk_score, self.assessment.custom_risk_score.colour
        else:
            inherent_risk_threshold_text = Threshold.objects.filter(lower_bound__lte=score, upper_bound__gte=score)
            if inherent_risk_threshold_text:
                return inherent_risk_threshold_text.first(), inherent_risk_threshold_text.first().colour

        return None, None

    def get_material_risk_source(self, material_risks):
        obj = {}
        for risk in material_risks:
            if risk['source'] in obj.keys():
                obj[risk['source']].extend([risk['name']])
            else:
                obj[risk['source']] = [risk['name']]
        return obj

    def show_document_questions(self, question_answered, questions):
        show_question = False

        for question in questions:
            if question['is_required']:
                show_question = True
                if question['answered']:
                    question_answered = True
            else:
                if question['answered']:
                    show_question = True
                    question_answered = True

        return show_question, question_answered

    def split_document_questions(self, questions):
        key_policy_questions = [q for q in questions if q.is_key_policy]
        other_questions = set(questions) - set(key_policy_questions)
        return key_policy_questions, other_questions

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.user.userprofile.company

        self.assessment = get_object_or_404(
            CompanyAssessment.objects.select_related(
                'created_by'
            ).select_related(
                'company_fund'
            ).select_related('custom_risk_score').prefetch_related('industries').prefetch_related('countries'),
            created_by__userprofile__company=company,
            slug=kwargs['slug']
        )

        context['company'] = company.name
        context['assessment'] = self.assessment
        context['company_name'] = self.assessment.company_name.replace('SASB:', '')

        industry_data = self.assessment.industries.all().values_list('slug', flat=True)
        country_list = self.assessment.countries.all().values_list('id', flat=True)
        top_5_impacts, overall_inherent_risk_score = calculate_top_5_impact_score(self.assessment.material_risks.all(), industry_data, country_list)

        risk_slugs = list(map(self.map_impact_slug, top_5_impacts))

        if self.assessment.answered_optional:
            context['rev_score'] = calculate_rev_counter_score(self.assessment)

        context['document_questions_complete'] = calculate_document_question_complete(self.assessment)

        context['risk_list'] = get_recommendations(top_5_impacts, self.assessment)

        context['other_issues_list'] = get_recommendations(
            self.assessment.issues.all().exclude(slug__in=risk_slugs),
            self.assessment
        )

        if self.assessment.issue_extra_description:
            context['other_issues_list'].append({
                'risk': self.assessment.issue_extra_title or 'Custom recommendations',
                'text': self.assessment.issue_extra_description
            })

        context['threshold'], context['risk_threshold_colour'] = self.get_threshold_colour_and_text(overall_inherent_risk_score)

        context['threshold_keys'] = Threshold.objects.all().order_by('lower_bound')

        active_version_list = [record.active_version.id for record in self.assessment.material_risks.all() if record.active_version]
        top_5_countries = calculate_top_5_at_risk_countrys(self.assessment.countries.all(), active_version_list, all=True)

        context['country_preparedness'] = get_country_preparedness(top_5_countries)
        context['top_5_countries'] = top_5_countries[:5]

        context['top_5_countries_risks'] = get_risks_for_top_5_countries(
            self.assessment.material_risks.filter(active_version__isnull=False),
            context['top_5_countries'],
        )

        context['top_5_impacts'] = top_5_impacts
        context['key_impacts'] = self.assessment.get_pdf_management_questions(company, top_5_impacts)

        material_risks = get_risk_by_source(self.assessment.material_risks.all(), industry_data)
        context['material_risk_source'] = self.get_material_risk_source(material_risks)
        context['user_added_material_risks'] = self.assessment.get_pdf_management_questions(company, [risk['id'] for risk in material_risks if risk['source'] == 'Client'])

        questions, _ = self.assessment.get_category_questions(company, category=None, risk_slugs=risk_slugs)
        optional_answered = False

        for question in questions:
            if question.hightlight is False and question.answer:
                optional_answered = True
                break

        if optional_answered:
            context['management_questions'] = len(questions)
        else:
            context['management_questions'] = len([question for question in questions if question.hightlight == True])

        context['management_questions_answered'] = sum(1 for question in questions if question.answer)
        context['management_insufficient'] = sum(1 for question in questions if question.insufficient)
        context['management_priority'] = sum(1 for question in questions if question.priority)

        document_questions = DocumentQuestion.objects.filter(pdf_display_order__isnull=False).order_by('pdf_display_order')
        for question in document_questions:
            answer = get_document_question_answer(self.assessment, question)
            if answer and answer.answer:
                question.answer = answer.answer
        context['market_leading'] = [question for question in document_questions if question.is_market_leading]
        context['best_practice'] = [question for question in document_questions if question.is_best_practice and not question.is_market_leading]
        context['is_key'] = [question for question in document_questions if question.is_key_policy]
        context['document_questions'] = self.split_document_questions(document_questions)
        context['document_answer_count'] = get_key_document_answer_count(self.assessment)

        context['sanctioned_countries'] = SanctionedCountry.objects.filter(country__id__in=country_list)

        try:
            context['data_uri'] = country_graph(self.assessment)
        except:
            context['data_uri'] = None

        context['risk_matrix'], context['risk_matrix_headers'] = get_risk_matrix(self.assessment.material_risks.all(), country_list, industry_data)
        try:
            header_length = len(context['risk_matrix_headers'][0]['industry_headers']) + len(context['risk_matrix_headers'][0]['country_headers'])

            if header_length > 6:
                context['risk_matrix_length'] = 100
            elif header_length == 5:
                context['risk_matrix_length'] = 80
            else:
                context['risk_matrix_length'] = 60
        except:
            context['risk_matrix_length'] = 60

        # Management questions
        context['environmental_questions'], context['environmental_questions_length'] = get_environmental_questions(questions, 'ENVIRONMENT', self.assessment)
        context['social_questions'], context['social_questions_length'] = get_environmental_questions(questions, 'SOCIAL', self.assessment)
        context['governance_questions'], context['governance_questions_length'] = get_environmental_questions(questions, 'GOVERNANCE', self.assessment)

        # Document checklist questions(
        document_environmental_questions, document_social_questions, document_governance_questions = get_and_split_document_questions(self.assessment)

        question_answered = False

        context['document_environmental_show'], question_answered = self.show_document_questions(
            question_answered,
            document_environmental_questions
        )

        context['document_social_show'], question_answered = self.show_document_questions(
            question_answered,
            document_social_questions
        )

        context['document_gov_show'], question_answered = self.show_document_questions(
            question_answered,
            document_governance_questions
        )

        context['document_checklist_answered'] = question_answered

        optional_doc_questions = list(DocumentQuestion.objects.filter(is_required=False,is_answerable=True).values_list('id', flat=True))
        document_optional_count = len(optional_doc_questions)
        optional_answered = DocumentQuestionAnswerSet.objects.filter(assessment=self.assessment, question__id__in=optional_doc_questions).count()

        if document_optional_count == optional_answered:
            context['show_market_leading_list'] = True

        context['contact_us'] = pdfContactDetail.objects.all().order_by('-id')[:8]

        context['document_environmental_questions'] = list(filter(self.filter_answered_or_required_questions, document_environmental_questions))
        context['document_social_questions'] = list(filter(self.filter_answered_or_required_questions, document_social_questions))
        context['document_governance_questions'] = list(filter(self.filter_answered_or_required_questions, document_governance_questions))

        if len(context['document_environmental_questions']) == 0:
            context['document_environmental_show'] = False

        if len(context['document_social_questions']) == 0:
            context['document_social_show'] = False

        if len(context['document_governance_questions']) == 0:
            context['document_gov_show'] = False

        return context
