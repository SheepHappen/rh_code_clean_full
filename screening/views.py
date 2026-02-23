import tablib

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import View, TemplateView
from django.http import JsonResponse, HttpResponse

from core.utils import get_category_color, get_score_colour
from company.models import Industry
from country.models import Country
from riskfactor.models import (
    IndustryRiskDataSet,
    MaterialityRisk,
    RiskDataSet,
    CountryRisk
)


class ScreeningView(LoginRequiredMixin, TemplateView):
    template_name = "screen.html"

    def get_context_data(self, **kwargs):
        kwargs.update({
            "risks": RiskDataSet.objects.all().order_by('name').values_list('name', flat=True),
            "industries": Industry.objects.all().order_by('name').values_list('name', flat=True),
            "countries": Country.objects.all().order_by('name').values_list('name', flat=True)
        })

        return super().get_context_data(**kwargs)

def get_industry(record):
    return record.industry.name

def get_version(record):
    return record.dataset_version.id

def Industry_comparison_table(request):
    selected_industries = request.GET.getlist('selected_industries[]')
    selected_risks = request.GET.getlist('selected_risks[]')
    risk_version = []
    risk_list = {}

    records = IndustryRiskDataSet.objects.filter(
        industry__id__in=selected_industries
    )

    table_header_data = list(map(get_industry, records))
    risk_version = list(map(get_version, records))

    dataset_risks = RiskDataSet.objects.filter(id__in=selected_risks).order_by('name')

    material_risks = MaterialityRisk.objects.filter(
        dataset_version__id__in=risk_version,
        risk_factor__id__in=selected_risks
    )

    for risk in dataset_risks:
        risk_list[risk.name] = [
            risk.name,
            risk.description
        ]

    for header in table_header_data:
        material_risks_in_header = [material for material in material_risks if material.industry.name == header]
        for risk in dataset_risks:
            added = False
            if material_risks:
                material_risk = [material for material in material_risks_in_header if material.risk_factor.name == risk.name]
                if material_risk:
                    added = True
                    risk_list[risk.name] = risk_list[risk.name] + [{
                        'score': material_risk[0].materiality,
                        'industry': header,
                        'risk_colour': get_score_colour(material_risk[0].materiality)
                    }]

            if not added:
                risk_list[risk.name] = risk_list[risk.name] + [{
                    'score': None,
                    'industry': header,
                }]

    return JsonResponse({
        't_head_data': table_header_data,
        't_body_data': risk_list
    })


def Geographic_comparison_table(request):
    selected_countries = request.GET.getlist('countries[]')
    selected_risks = request.GET.getlist('risks[]')

    countries = Country.objects.filter(name__in=selected_countries).values('name', 'id').order_by('name')
    records = RiskDataSet.objects.filter(id__in=selected_risks).order_by('name')

    risk_list = {}

    selected_countries = [country['id'] for country in countries]
    table_header_data = [country['name'] for country in countries]

    for record in records:
        risk_list[record.name] = [record.name, record.description]
        if record.active_version:
            for item in record.active_version.countryrisk_set.filter(country__id__in=selected_countries).order_by('country__name'):
                country = item.country.name
                if country and country in table_header_data:
                    exposure = item.exposure

                    if exposure:
                        risk_list[record.name] = risk_list[record.name] + [{
                            'score': exposure,
                            'country': country,
                            'risk_colour': get_score_colour(exposure)
                        }]

    return JsonResponse({
        't_head_data': table_header_data,
        't_body_data': risk_list
    })


def get_risk_by_source(selected_risks, selected_industries=None):
    risk_list = []
    selected_risk_ids = [risk.id for risk in selected_risks]
    if selected_industries:
        industries = Industry.objects.filter(id__in=selected_industries)
        added_list = []
        for industry in industries:
            if industry.industryriskdataset_set.first() and industry.industryriskdataset_set.first().dataset_version:
                risks = industry.industryriskdataset_set.first().dataset_version.materialityrisk_set.filter(
                    risk_factor__id__in=selected_risk_ids
                ).order_by('risk_factor__name')
                for risk in risks:
                    if risk.risk_factor_id not in added_list:
                        colour = get_category_color(risk.risk_factor.category)
                        risk_list.append(
                            {
                                'id': risk.risk_factor_id,
                                'text': "{},{}".format(colour, risk.risk_factor.name),
                                'source': risk.source.name,
                                'name': risk.risk_factor.name
                            }
                        )
                        selected_risk_ids.remove(risk.risk_factor_id)
                        added_list.append(risk.risk_factor_id)
        for risk in selected_risks:
            if risk.id in selected_risk_ids:
                risk_list.append({
                    'id': risk.id,
                    'text': risk.name,
                    'source': 'Client',
                    'name': risk.name
                })
    else:
        risk_list = [{'id': risk.id, 'text': risk.name, 'source': 'Client', 'name': risk.name} for risk in selected_risks]

    return risk_list


def Industry_select(request):
    selected_industries = request.POST.getlist('industry[]')
    material_risk_list = []
    added_list = []

    for selected_industry in selected_industries:
        industry = Industry.objects.get(pk=int(selected_industry))
        if industry.industryriskdataset_set.first() and industry.industryriskdataset_set.first().dataset_version:
            risks = industry.industryriskdataset_set.first().dataset_version.materialityrisk_set.all().order_by('risk_factor__name')
            for risk in risks:
                if risk.risk_factor_id not in added_list:
                    colour = get_category_color(risk.risk_factor.category)
                    material_risk_list.append(
                        {
                            'id': risk.risk_factor_id,
                            'text': "{},{}".format(colour, risk.risk_factor.name),
                        }
                    )
                    added_list.append(risk.risk_factor_id)

    return JsonResponse({'risks': material_risk_list})


class dataCsv(LoginRequiredMixin, View):
    def create_int_list(self, records):
        records = list(set(records.split(',')))
        return [int(record) for record in records if record]

    def create_headers(self, industries=None, countries=None):
        headers = []
        headers.append('Risk')
        if industries:
            headers.append('Industry')
            headers.append('Industry Score')
            for index, value in enumerate(industries):
                if index > 0:
                    headers.append('Industry')
                    headers.append('Industry Score')

        if countries:
            headers.append('Country')
            headers.append('Country Score')

            for index, value in enumerate(countries):
                if index > 0:
                    headers.append('Country')
                    headers.append('Country Score')

        return headers

    def post(self, request):
        risks_list = request.POST.getlist('risk_id[]')
        industries_list = request.POST.getlist('industry_ids[]', None)
        countries_list = request.POST.getlist('country_ids[]', None)

        industries_list = industries_list[0].split(',')
        countries_list = countries_list[0].split(',')
        risks_list = risks_list[0].split(',')

        countries = None
        industries = None

        risks = RiskDataSet.objects.filter(id__in=risks_list).order_by('name')

        if countries_list and '' not in countries_list:
            countries = Country.objects.filter(name__in=countries_list).order_by('name')
            data = tablib.Dataset(
                headers=self.create_headers(industries=None, countries=countries_list)
            )
        else:
            industries = Industry.objects.filter(id__in=industries_list)

            data = tablib.Dataset(
                headers=self.create_headers(industries=industries_list, countries=None)
            )

        for risk in risks:
            data_list = []
            data_list.append(risk.name)

            if industries:
                for industry in industries:
                    industry_data = IndustryRiskDataSet.objects.get(industry=industry)
                    data_list.append(industry.name)
                    score = 'N/A'
                    if industry_data.dataset_version:
                        industry_risk = MaterialityRisk.objects.filter(
                            industry=industry,
                            dataset_version=industry_data.dataset_version,
                            risk_factor__id=risk.id
                        )
                        if industry_risk:
                            score = industry_risk[0].materiality

                    data_list.append(score)

            if countries:
                for country in countries:
                    data_list.append(country.name)
                    score = 'N/A'
                    if risk.active_version:
                        country_risk = CountryRisk.objects.filter(
                            country=country,
                            version__id=risk.active_version.id
                        )
                        if country_risk and country_risk[0].exposure:
                            score = country_risk[0].exposure

                    data_list.append(score)

            data.append(data_list)
        response = HttpResponse(data.export('xlsx'), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

        if countries:
            filename = 'comparison_country.xlsx'
        else:
            filename = 'comparison_industry.xlsx'

        response['Content-Disposition'] = 'attachment; filename="{}'.format(filename)

        return response
