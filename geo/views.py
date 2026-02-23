import datetime
import json
import tablib
import pytz

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.views.generic import View
from django.utils.safestring import mark_safe

from core.models import Threshold
from core.utils import is_ajax
from company.models import CompanyAssessment
from country.models import Country
from riskfactor.models import RiskDataSet, CountryRisk


def filter_map_by_fund_and_country(fund, company, company_name):
    company_selected_country_names = []
    fund_assessments = CompanyAssessment.objects.filter(
        created_by__userprofile__company__name=company_name,
        company_fund__enabled=True
    ).select_related('created_by').select_related(
        'company_fund'
    ).select_related('parent').select_related('custom_risk_score')

    if fund != "all_funds":
        fund_assessments = fund_assessments.filter(company_fund__slug=fund)
        if company != "all_companies":
            fund_assessments = fund_assessments.filter(slug=company)
    else:
        if company != "all_companies":
            fund_assessments = CompanyAssessment.objects.filter(
                slug=company
            ).select_related('created_by').select_related(
                'company_fund'
            ).select_related('parent').select_related('custom_risk_score')

    for fund_assessment in fund_assessments:
        company_selected_country_names.extend(list(fund_assessment.countries.all().values_list('name', flat=True)))

    return company_selected_country_names


def get_country_risk_exposure(risk, country):
    countryRisk = CountryRisk.objects.filter(
        version=risk.active_version,
        country__name=country
    ).select_related('country').select_related('version').first()
    if countryRisk and countryRisk.exposure is not None:
        return countryRisk.exposure

    return 'N/A'


class GeoAssessmentView(LoginRequiredMixin, View):
    template_name = "geo_assessment.html"

    def get_initial_data(self, all_countries):
        countries = []
        numbers = []
        countryNames = []

        for country in all_countries:
            countries.append(country['iso3'])
            numbers.append(0)
            countryNames.append(mark_safe("<b>{}</b>".format(country['name'])))

        return json.dumps(countries), json.dumps(numbers), json.dumps(countryNames)

    def get(self, request, pk=None):
        if is_ajax(request=request):
            all_countries = Country.objects.all().exclude(name='Antarctica').values('name', 'iso3')
            company_selected = request.GET.get('company_filter', None)
            company_selected_country_names = []
            fund_selected = request.GET.get('fund_filter', None)

            keys = list(Threshold.objects.all().order_by('lower_bound'))

            countries = []
            numbers = []
            countryNames = []

            colour_scale = [[0, 'rgb(135,135,135)']]
            colour_dict = {}

            # plotly colour scale. last number must be 1 for it to work.
            for idx, num in enumerate((x * 0.1 for x in range(1, 11))):
                if idx == len(keys):
                    break
                if idx == len(keys) - 1:
                    num = 1
                else:
                    num = round(num, 2)
                colour_scale.append([num, keys[idx].colour])
                colour_dict[keys[idx].text] = num

            risk = RiskDataSet.objects.get(slug=request.GET.get('risk'))

            if fund_selected:
                company_selected_country_names = filter_map_by_fund_and_country(fund_selected, company_selected, request.user.userprofile.company.name)

            for country in all_countries:
                exposure = 'N/A'
                country_name = country['name']

                if country_name not in company_selected_country_names and (company_selected or fund_selected):
                    numbers.append(0)

                if country_name in company_selected_country_names or (company_selected is None or fund_selected is None):
                    exposure = get_country_risk_exposure(risk, country_name)

                    if exposure == 'N/A':
                        numbers.append(0)
                    else:
                        exposure = round(exposure, 1)
                        threshold_text = Threshold.objects.filter(lower_bound__lte=exposure, upper_bound__gte=exposure)
                        threshold_text = threshold_text[0].text
                        get_matching_obj = colour_dict.get(threshold_text)
                        if get_matching_obj:
                            numbers.append(get_matching_obj)

                countries.append(country['iso3'])
                countryNames.append(mark_safe("<b>{}</b> <br> {}: {} <br>".format(country_name, risk.name, exposure)))

            return JsonResponse({
                'countries': json.dumps(countries),
                'numbers': json.dumps(numbers),
                'countryNames': json.dumps(countryNames),
                'colourScale': json.dumps(colour_scale),
            })

        else:
            risks = RiskDataSet.objects.filter(
                category__slug__in=['environmental', 'social', 'governance']
            ).select_related('category')

            environmental_risks = [{'name': risk.name, 'slug': risk.slug} for risk in risks if risk.category.slug == 'environmental']
            social_risks = [{'name': risk.name, 'slug': risk.slug} for risk in risks if risk.category.slug == 'social']
            governance_risks = [{'name': risk.name, 'slug': risk.slug} for risk in risks if risk.category.slug == 'governance']

            all_countries = Country.objects.all().exclude(name='Antarctica').values('name', 'iso3')

            countries, numbers, countryNames = self.get_initial_data(all_countries)

            funds = request.user.userprofile.company.companyfund_set.filter(enabled=True)

            companies = CompanyAssessment.objects.filter(
                created_by__userprofile__company__name=request.user.userprofile.company.name
            ).select_related('created_by').select_related(
                'company_fund'
            ).select_related('parent').select_related(
                'custom_risk_score'
            ).values_list('slug', 'company_name')

            keys = Threshold.objects.all().order_by('lower_bound')

            return render(request, self.template_name, locals())


class assessmentDataDownload(LoginRequiredMixin, View):
    def get(self, request):
        risk = RiskDataSet.objects.get(slug=request.GET.get('risk'))
        fund = request.GET.get('fund', None)
        funds = None
        company = request.GET.get('company', None)

        all_countries = Country.objects.all().order_by('name')

        if fund:
            company_selected_country_names = filter_map_by_fund_and_country(fund, company, request.user.userprofile.company.name)
            all_countries = [record for record in all_countries if record.name in company_selected_country_names]
            funds = request.user.userprofile.company.companyfund_set.filter(enabled=True)
            if fund != 'all_funds':
                funds = funds.filter(slug=fund)

            company_assessments = CompanyAssessment.objects.filter(
                created_by__userprofile__company__name=request.user.userprofile.company.name
            ).select_related('created_by').select_related(
                'company_fund'
            ).select_related('parent').select_related('custom_risk_score')

            if company != 'all_companies':
                company_assessments = company_assessments.filter(slug=company)

        risk_list = ['Risk factor:', risk.name]
        category_list = ['Category:', risk.category]
        description_list = ['Description:', risk.description]
        source_list = ['Datasource:', risk.active_version]
        dateTime = datetime.datetime.now(pytz.timezone('Europe/London'))
        time_list = ['Time:', dateTime.strftime('%Y-%m-%d %H:%M:%S')]
        country_headings = ['Country', 'Score']
        funds_list = ['Fund(s):']
        company_list = ['Company(s):']

        length_list = 0
        blank_list = []
        if funds:
            for record in funds:
                funds_list.append(record.name)

            for record in company_assessments:
                company_list.append(record.company_name)

            company_list_length = len(company_list)
            fund_list_length = len(funds_list)

            if company_list_length > fund_list_length:
                length_list = company_list_length - 2
            else:
                length_list = fund_list_length - 2

            blank_list = [''] * length_list

            risk_list = risk_list + blank_list
            category_list = category_list + blank_list
            source_list = source_list + blank_list
            time_list = time_list + blank_list
            description_list = description_list + blank_list
            country_headings = country_headings + blank_list

            company_length_list = len(country_headings) - len(company_list)
            company_blank_list = [''] * company_length_list
            company_list = company_list + company_blank_list

            fund_length_list = len(country_headings) - len(funds_list)
            fund_blank_list = [''] * fund_length_list
            funds_list = funds_list + fund_blank_list

        data = tablib.Dataset()

        data.append(risk_list)
        data.append(category_list)
        data.append(description_list)
        data.append(source_list)
        data.append(time_list)

        if funds:
            data.append(funds_list)
            data.append(company_list)
        data.append([])

        data.append(country_headings)

        for country in all_countries:
            exposure = get_country_risk_exposure(risk, country.name)

            country_list = [country.name, exposure]
            if funds:
                country_list = country_list + blank_list

            data.append(country_list)

        response = HttpResponse(data.export('xlsx'), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

        if funds:
            response['Content-Disposition'] = 'attachment; filename=" geographic_assessment_custom_.xlsx"'
        else:
            response['Content-Disposition'] = 'attachment; filename="geographic_assessment.xlsx"'

        return response


class assessmentDataDownloadAll(LoginRequiredMixin, View):
    def set_risk_names(self, risks):
        risk_names = []
        risk_categories = []
        risk_sources = []
        for risk in risks:
            risk_names.append(risk.name)
            risk_categories.append(risk.category)
            risk_sources.append(risk.active_version)

        return risk_names, risk_categories, risk_sources

    def get(self, request):
        risks = RiskDataSet.objects.filter(
            category__slug__in=['environmental', 'social', 'governance']
        )

        environmental_risks = [risk for risk in risks if risk.category.slug == 'environmental']
        social_risks = [risk for risk in risks if risk.category.slug == 'social']
        governance_risks = [risk for risk in risks if risk.category.slug == 'governance']

        all_countries = Country.objects.all().order_by('name')
        dateTime = datetime.datetime.now(pytz.timezone('Europe/London'))
        data = tablib.Dataset()

        risk_names = ['Risk factor:']
        risk_categories = ['Description:']
        risk_sources = ['Datasource:']

        for risks in [environmental_risks, social_risks, governance_risks]:
            name, cat, sources = self.set_risk_names(risks)
            risk_names = risk_names + name
            risk_categories = risk_categories + cat
            risk_sources = risk_sources + sources

        data.append(risk_names)
        data.append(risk_categories)
        data.append(risk_sources)

        dateTime = datetime.datetime.now(pytz.timezone('Europe/London'))
        time_row = ['Time:', dateTime.strftime('%Y-%m-%d %H:%M:%S')]
        country_headings = ['Country', '']

        length_list = len(risk_names) - 2
        blank_list = [''] * length_list

        time_row = time_row + blank_list
        country_headings = country_headings + blank_list

        data.append(time_row)
        data.append([])
        data.append(country_headings)

        for country in all_countries:
            country_list = [country.name]
            for risk in environmental_risks + social_risks + governance_risks:
                exposure = 'N/A'

                countryRisk = CountryRisk.objects.filter(
                    version=risk.active_version,
                    country=country
                ).select_related('version').prefetch_related('country')

                if countryRisk and countryRisk[0].exposure is not None:
                    exposure = countryRisk[0].exposure

                country_list.append(exposure)
            data.append(country_list)

        response = HttpResponse(data.export('xlsx'), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="geographic_assessment.xlsx"'

        return response
