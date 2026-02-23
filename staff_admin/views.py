from datetime import datetime
from decimal import Decimal
import json

import tablib
from sendfile import sendfile

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import View, TemplateView

from country.models import Country

from riskfactor.models import RiskDataSet, RiskDataSetVersion
from riskfactor.importer import GeoExposureRawImporter
from riskfactor.utils import create_min_max, f_positive_1_100, do_skew
from .forms import UploadForm
from .mixins import StaffAccessMixin


def create_skew_data(skew, version):
    value_data = []
    for item in version.countryrisk_set.all():
        if item.exposure:
            item.exposure = float(item.exposure)

        value_data.append(
            {
                'id': item.id,
                'name': item.country.name,
                'value': item.exposure
            }
        )

    data = f_positive_1_100(value_data)

    for value in data:
        value['value'] = do_skew(value['value'], skew)

    v_min, v_max = create_min_max(data)

    return data, v_min, v_max


def calculate_skew(exposure, v_min, v_max, origional_data_order, data_order):
    value = 10.0 * (float(exposure) - v_min) / (v_max - v_min)

    # tie back to boundary
    value = min(10.0, value)
    value = max(0.0, value)

    if origional_data_order == 'ASC' and data_order == 'DESC' or origional_data_order == 'DESC' and data_order == 'ASC':
        value = 10.0 - value

    return value


def get_rating(exposure):
    if exposure is None or isinstance(exposure, str):
        return 'No data'
    if exposure <= 1:
        return 'Very Low'
    elif exposure <= 2:
        return 'Low'
    elif exposure <= 4:
        return 'Medium'
    elif exposure <= 6:
        return 'Medium to high'
    elif exposure <= 8:
        return 'High'
    elif exposure > 8:
        return 'Very High'


class StaffAdminView(LoginRequiredMixin, StaffAccessMixin, TemplateView):
    template_name = "staff_home.html"


class UploadView(LoginRequiredMixin, StaffAccessMixin, View):
    template_name = "upload.html"

    def get(self, request):
        form = UploadForm()
        return render(request, self.template_name, locals())

    def generate_data(self, version, skew, origional_data_order, data_order):
        records = []
        headers = ['Country', 'Score', 'Rating']
        graph_dict = {}

        if skew and skew != 'NONE':
            data, v_min, v_max = create_skew_data(skew, version)

        for record in version.countryrisk_set.all():
            if record.exposure or record.exposure == 0:
                exposure = record.exposure
                if skew != 'NONE':
                    skew_exposure = [d['value'] for d in data if d['id'] == record.id]
                    try:
                        exposure = calculate_skew(
                            skew_exposure[0],
                            v_min,
                            v_max,
                            origional_data_order,
                            data_order
                        )
                    except:
                        exposure = 'Null'
                elif data_order:
                    if origional_data_order == 'ASC':
                        if data_order == 'DESC':
                            exposure = Decimal(10) - exposure
                    if origional_data_order == 'DESC':
                        if data_order == 'ASC':
                            exposure = Decimal(10) - exposure

                if not isinstance(exposure, str):
                    exposure = round(exposure, 3)
            else:
                exposure = 'Null'

            graph_dict[record.country.name] = str(exposure)
            records.append([record.country.name, exposure, get_rating(exposure)])

        return records, headers, graph_dict

    def post(self, request, *args, **kwargs):
        items = {
            'need_doc': 'No'
        }
        form = UploadForm(request.POST, request.FILES, items=items)

        skew = request.POST.get("skew")
        data_order = request.POST.get("data_order")

        if 'update-graph' in request.POST:
            version = RiskDataSetVersion.objects.get(
                id=request.POST.get("version_id")
            )
            version_id = version.id
            origional_data_order = request.POST.get('origional_data_order')
            records, headers, graph_dict = self.generate_data(
                version,
                skew=skew,
                origional_data_order=origional_data_order,
                data_order=data_order
            )

            graph = json.dumps(graph_dict)

        if 'validate' in request.POST and form.is_valid():
            risk_factor = RiskDataSet.objects.filter(name=request.POST['risk_factor']).first()
            name = "{}_{}".format(datetime.now().strftime("%Y_%m_%d"), risk_factor.slug)

            if RiskDataSetVersion.objects.filter(name=name).exists():
                name = "{}_{}".format(datetime.now().strftime("%Y_%m_%d%H%M%S"), risk_factor.slug)

            version_data = {
                'name': name,
                'reference': form.cleaned_data['reference'],
                'url': form.cleaned_data['url'],
                'description': form.cleaned_data['description']
            }

            importer = GeoExposureRawImporter(
                document=form.cleaned_data['document'],
                version_data=version_data,
                data_order=form.cleaned_data['data_order'],
                normalise_data=form.cleaned_data['normalise_data'],
                skew=form.cleaned_data['skew'],
                start_row=form.cleaned_data['start_row'],
                ignore_empty_data=form.cleaned_data['ignore_empty_data'],
                col_country=int(form.cleaned_data['col_country']),
                col_data=int(form.cleaned_data['col_data']),
            )
            importer.read()
            importer.process()
            importer.save()

            error_list = importer.error_data

            version = importer.version_obj
            version_id = version.id
            risk_factor.versions.add(version)
            risk_factor.save()

            origional_data_order = data_order
            records, headers, graph_dict = self.generate_data(version, skew=skew, origional_data_order=origional_data_order, data_order=data_order)

            graph = json.dumps(graph_dict)

        return render(request, self.template_name, locals())


def confirm_upload(request, version_id):
    risk_factor = RiskDataSet.objects.filter(name=request.POST['risk_factor']).first()
    version = RiskDataSetVersion.objects.get(id=version_id)
    skew = request.POST.get("skew")
    data_order = request.POST.get("data_order")
    origional_data_order = request.POST.get("origional_data_order")

    if skew and skew != 'NONE':
        data, v_min, v_max = create_skew_data(skew, version)

    for item in version.countryrisk_set.all():
        if item.exposure or item.exposure == 0:
            if skew and skew != 'NONE':
                skew_exposure = [d['value'] for d in data if d['id'] == item.id]
                try:
                    item.exposure = calculate_skew(
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
                    item.exposure = Decimal(10) - item.exposure

            item.save()
        risk_factor.active_version = version
        version.skew = skew
        version.data_order = data_order
        version.save()
        risk_factor.save()

    messages.add_message(request, messages.SUCCESS, "Successfully imported")

    return HttpResponseRedirect(reverse("upload"))


class dataCountryTemplate(LoginRequiredMixin, View):
    def post(self, request):
        data = tablib.Dataset(headers=['Country', 'Score'])

        countries = Country.objects.all()

        for country in countries:
            data.append([country.name, ''])

        response = HttpResponse(data.export('xlsx'), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

        response['Content-Disposition'] = 'attachment; filename="risk_upload_template.xlsx"'

        return response


class DownloadFile(LoginRequiredMixin, View):
    def get(self, request, pk):
        version = RiskDataSetVersion.objects.get(pk=pk)
        return sendfile(request, version.file_obj.path, attachment=True, attachment_filename=version.filename())
