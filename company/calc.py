import decimal

from company.models import DocumentQuestionAnswerSet
from core.models import DocumentQuestion
from riskfactor.models import CountryRisk, MaterialityRisk, IndustryRiskDataSet
from core.utils import get_score_colour

from itertools import repeat
from pprint import pprint


def calculate_category_score(assessment, questions, category, multiplier=0.33):
    score = 0

    if questions:
        question_length = 0
        for question in questions:
            if question.category == category:
                assessment_answers = question.documentquestionanswerset_set.filter(assessment=assessment)
                if question.yes_score or question.no_score:
                    question_length += 1
                for answer in assessment_answers:
                    if question.yes_score and answer.answer == 'Y' or question.no_score and answer.answer == 'N':
                        score += 1
        if question_length > 0 and score > 0:
            percentage = score / question_length * 100

            return percentage * multiplier
        else:
            return 0

    return score


def calculate_rev_counter_score(assessment):
    questions = DocumentQuestion.objects.filter(
        is_answerable=True
    ).prefetch_related('documentquestionanswerset_set')
    score = 0

    for category in ['ENVIRONMENT', 'SOCIAL', 'GOVERNANCE']:
        multiplier = 0.33
        if category == 'GOVERNANCE':
            multiplier = 0.34

        score = score + calculate_category_score(assessment, questions, category, multiplier)

    return int(score)


def calculate_document_question_complete(assessment):
    questions = DocumentQuestion.objects.filter(is_answerable=True).prefetch_related('documentquestionanswerset_set')

    percentage_complete = 0
    score = 0

    if questions:
        question_length = questions.count()
        for question in questions:
            assessment_answers = question.documentquestionanswerset_set.filter(assessment=assessment)
            for answer in assessment_answers:
                if answer.answer:
                    score += 1
                if answer.answer in ['N', 'X']:
                    question_length = question_length - len(question.documentquestion_set.all())

        if question_length > 0 and score > 0:
            percentage_complete = score / question_length * 100

        return int(round(percentage_complete, 2))

    return 0


class CountryObj(object):
    name = ""
    score = 0
    obj_id = ''
    colour = ''

    def __init__(self, name, score, obj_id):
        self.name = name
        self.score = score
        self.obj_id = obj_id
        self.colour = get_score_colour(score)


class ImpactObj(object):
    obj_id = ''
    name = ""
    score = 0
    recommendation = ""
    description = ""
    slug = ''
    colour = ''

    def __init__(self, name, score, obj_id, recommendation, description, slug):
        self.name = name
        self.score = score
        self.obj_id = obj_id
        self.recommendation = recommendation
        self.description = description
        self.slug = slug
        self.colour = get_score_colour(score)


def calculate_top_5_at_risk_countrys(countries, version_list, all=False):
    country_list = []

    for country in countries:
        risks = CountryRisk.objects.filter(
            country=country,
            version_id__in=version_list,
        )
        done_list = []
        exposure = []
        for risk in risks:
            if risk.version_id.hex not in done_list:
                if risk.exposure is not None:
                    exposure.append(risk.exposure)
                done_list.append(risk.version_id.hex)

        try:
            country.risk_score = sum(exposure) / len(exposure)
        except:
            country.risk_score = 0.0

        country_list.append(
            CountryObj(country.name, country.risk_score, country.id)
        )

    country_list = sorted(country_list, key=lambda x: x.score, reverse=True)

    if all:
        return country_list
    else:
        return country_list[:5]


def average_industry_risk_score(industry_slugs, version_id, risk):
    industry_risks = MaterialityRisk.objects.filter(
        industry__slug__in=industry_slugs,
        dataset_version__id__in=version_id,
        risk_factor_id=risk
    )

    materiality = [record.materiality for record in industry_risks if record.materiality]

    if materiality:
        return sum(materiality) / len(materiality)


def calculate_top_5_impact_score(risks, industry_slugs, countries, all_records=False, other_recommendations=False):
    impact_list = []
    industry_version_ids = IndustryRiskDataSet.objects.filter(industry__slug__in=industry_slugs).values_list(
        'dataset_version_id', flat=True
    )
    overall_inherent_risk_score = 0
    for risk in risks:
        country_average_risk_score = None
        industry_average_risk_score = average_industry_risk_score(industry_slugs, list(industry_version_ids), risk.id)
        done_list = []
        if risk.active_version:
            country_risks = CountryRisk.objects.filter(
                country__id__in=countries,
                version__id=risk.active_version_id
            ).distinct()
            if country_risks:
                exposure = []
                for record in country_risks:
                    if record.country_id not in done_list:
                        if record.exposure is not None:
                            exposure.append(record.exposure)
                        done_list.append(record.country_id)

                if exposure:
                    country_average_risk_score = sum(exposure) / len(exposure)

        if country_average_risk_score and industry_average_risk_score:
            score = (float(industry_average_risk_score) + float(country_average_risk_score)) / 2

            impact_list.append(
                ImpactObj(risk.name, score, risk.id, risk.recommendation, risk.pdf_description, risk.slug)
            )
        else:
            if other_recommendations:
                if country_average_risk_score:
                    impact_list.append(
                        ImpactObj(risk.name, country_average_risk_score, risk.id, risk.recommendation, risk.pdf_description, risk.slug)
                    )
                if industry_average_risk_score:
                    impact_list.append(
                        ImpactObj(risk.name, industry_average_risk_score, risk.id, risk.recommendation, risk.pdf_description, risk.slug)
                    )

    impact_list = sorted(impact_list, key=lambda x: x.score, reverse=True)

    average_list = [float(impact.score) for impact in impact_list[:5]]

    if average_list:
        overall_inherent_risk_score = sum(average_list) / len(average_list)

    if not all_records:
        impact_list = impact_list[:5]

    return impact_list, overall_inherent_risk_score
