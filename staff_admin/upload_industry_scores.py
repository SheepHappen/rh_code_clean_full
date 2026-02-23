from decimal import Decimal
import json

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import View

from riskfactor.models import RiskDataSetVersion, IndustryRiskDataSet
from riskfactor.importer import SectorImporter
from riskfactor.utils import create_min_max, f_positive_1_100, do_skew
from .utils import calculate_skew, get_rating
from .forms import UploadForm
from .mixins import StaffAccessMixin


def create_skew_data(skew, versions):
    value_data = []
    for version in versions:
        for item in version.materialityrisk_set.all():
            value_data.append(
                {
                    'risk': item.risk_factor.id,
                    'industry': item.industry.id,
                    'value': item.materiality,
                }
            )

    data = f_positive_1_100(value_data)

    for value in data:
        value['value'] = do_skew(value['value'], skew)

    v_min, v_max = create_min_max(data)

    return data, v_min, v_max


class UploadIndustryView(LoginRequiredMixin, StaffAccessMixin, View):
    template_name = "upload-industry.html"

    def get(self, request):
        items = {
            'form_type': 'Sector',
        }
        form = UploadForm(items=items)
        return render(request, self.template_name, locals())

    def generate_data(self, data_set, skew, origional_data_order, data_order):
        records = []
        headers = ['Industry', 'Risk factor', 'Source', 'Materiality', 'score']
        graph_dict = {}

        if skew and skew != 'NONE':
            data, v_min, v_max = create_skew_data(skew, data_set)

        for item in data_set:
            for record in item.materialityrisk_set.all():
                if record.materiality or record.materiality == 0:
                    score = record.materiality
                    if skew != 'NONE':
                        skew_exposure = [d['value'] for d in data if d['risk'] == record.risk_factor_id and d['industry'] == record.industry_id]
                        try:
                            score = calculate_skew(
                                skew_exposure[0],
                                v_min,
                                v_max,
                                origional_data_order,
                                data_order
                            )
                        except:
                            score = 'Null'
                    elif data_order:
                        if origional_data_order == 'ASC':
                            if data_order == 'DESC':
                                score = Decimal(10) - score
                        if origional_data_order == 'DESC':
                            if data_order == 'ASC':
                                score = Decimal(10) - score

                    if not isinstance(score, str):
                        score = round(score, 3)
                else:
                    score = 'Null'

                label = "{}/{}".format(record.industry.name, record.risk_factor.name)
                graph_dict[label] = str(score)
                records.append([
                    record.industry.name,
                    record.risk_factor.name,
                    record.source.name,
                    score,
                    get_rating(score)
                ])

        return records, headers, graph_dict

    def post(self, request, *args, **kwargs):
        items = {
            'form_type': 'Sector',
            'need_doc': 'No'
        }
        form = UploadForm(request.POST, request.FILES, items=items)

        skew = request.POST.get("skew")
        data_order = request.POST.get("data_order")

        if 'update-graph' in request.POST:
            risk_data_sets = request.POST.get("risk_data_sets")
            version_id = request.POST.get("version_id")
            post_versions = version_id.split(",")
            versions = RiskDataSetVersion.objects.filter(
                id__in=post_versions
            )
            origional_data_order = request.POST.get('origional_data_order')
            records, headers, graph_dict = self.generate_data(
                versions,
                skew=skew,
                origional_data_order=origional_data_order,
                data_order=data_order
            )
            graph = json.dumps(graph_dict)

        if 'validate' in request.POST and form.is_valid():
            version_data = {
                'reference': form.cleaned_data['reference'],
                'url': form.cleaned_data['url'],
                'description': form.cleaned_data['description']
            }

            importer = SectorImporter(
                document=form.cleaned_data['document'],
                version_data=version_data,
                data_order=form.cleaned_data['data_order'],
                normalise_data=form.cleaned_data['normalise_data'],
                skew=form.cleaned_data['skew'],
                start_row=form.cleaned_data['start_row'],
                ignore_empty_data=form.cleaned_data['ignore_empty_data'],
            )
            importer.read()
            importer.process()
            importer.save()

            versions = importer.version_objs
            version_id = [str(version.id) for version in versions]
            version_id = ', '.join(version_id)
            risk_data_sets = importer.risk_data_sets
            risk_data_sets = ', '.join(risk_data_sets)
            origional_data_order = data_order
            records, headers, graph_dict = self.generate_data(versions, skew=skew, origional_data_order=origional_data_order, data_order=data_order)

            graph = json.dumps(graph_dict)

        return render(request, self.template_name, locals())


def publish_industry_values(request):
    data_set_ids = request.POST.get("risk_data_sets").split(",")
    data_set_ids = [data for data in data_set_ids]

    data_sets = IndustryRiskDataSet.objects.all()

    post_versions = request.POST.get("version_id").split(",")
    post_versions = [version.replace('-', '') for version in post_versions]

    for data_set in data_sets:
        for version in data_set.versions.all():
            if version.id.hex in post_versions:
                data_set.dataset_version = version
                data_set.save()

    skew = request.POST.get("skew")
    data_order = request.POST.get("data_order")
    origional_data_order = request.POST.get("origional_data_order")

    versions = RiskDataSetVersion.objects.filter(id__in=post_versions)

    if skew and skew != 'NONE':
        data, v_min, v_max = create_skew_data(skew, versions)

    for version in versions:
        for item in version.materialityrisk_set.all():
            if item.materiality or item.materiality == 0:
                if skew and skew != 'NONE':
                    skew_exposure = [d['value'] for d in data if d['risk'] == item.risk_factor_id and d['industry'] == item.industry_id]
                    try:
                        item.materiality = calculate_skew(
                            skew_exposure[0],
                            v_min,
                            v_max,
                            origional_data_order,
                            data_order
                        )
                    except:
                        pass
                else:
                    if origional_data_order == 'ASC' and data_order == 'DESC' or origional_data_order == 'DESC' and data_order == 'ASC':
                        item.materiality = Decimal(10) - item.materiality
                item.save()

    messages.add_message(request, messages.SUCCESS, "Successfully imported")

    return HttpResponseRedirect(reverse("industry_risk_factor_values"))
