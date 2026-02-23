from datetime import datetime
import logging
import tablib
import uuid

from django.db import transaction
from django.db.models import Q
from country.models import Country

from riskfactor.models import (
    RiskDataSetVersion,
    CountryRisk,
    IndustryRiskDataSet,
    RiskDataSet,
    MaterialityRisk,
    RiskDataSetSource
)
from riskfactor.utils import create_min_max, do_skew, f_positive_1_100, fmt_4dp

from company.models import Industry


def in_dict_list(key, value, my_list):
    for this in my_list:
        if this[key].lower() == value.lower():
            return this
    return {}


class GeoExposureRawImporter(object):
    def __init__(self, *args, **kwargs):
        self.start_row = kwargs.get('start_row', 1)
        self.col_country = kwargs.get('col_country', 0)
        self.col_data = kwargs.get('col_data', 1)

        self.normalise_data = kwargs.get('normalise_data', False)
        self.ignore_empty_data = kwargs.get('ignore_empty_data', False)

        self.version_data = kwargs.pop('version_data', {})
        self.riskfactor = kwargs.pop('riskfactor', None)
        self.skew = kwargs.pop('skew', None)
        self.data_order = kwargs.pop('data_order', 'ASC')

        self._data = []
        self._file = kwargs.pop('document')

        countries = Country.objects.all()
        country_lookup = []
        for country in countries:
            country_lookup.append({
                'name': country.name,
                'id': country.id
            })

        self.country_lookup = country_lookup

    def read(self):
        imported_data = tablib.Dataset().load(self._file)

        for (line_no, row) in enumerate(imported_data):
            if line_no < int(self.start_row):
                logging.debug('skipping: {}'.format(row))
                continue

            country_name = row[self.col_country].strip()
            risk_value = row[self.col_data]

            if isinstance(country_name, list):
                country_name = [name.lower() for name in country_name]
            else:
                country_name = country_name.lower()

            if self.ignore_empty_data:
                if not country_name or not risk_value:
                    continue

            country = in_dict_list('name', country_name, self.country_lookup)
            if country:
                try:
                    risk_value = float(risk_value)
                    self._data.append(
                        {
                            'id': country['id'],
                            'name': country['name'],
                            'value': risk_value
                        }
                    )
                except:
                    self._data.append(
                        {
                            'id': 'blank',
                            'name': country_name,
                            'value': risk_value
                        }
                    )
            else:
                self._data.append(
                    {
                        'id': 'blank',
                        'name': country_name,
                        'value': None
                    }
                )

    def process(self):
        '''
        normalise values so they end up being between 0 and 10
        this is done on the 5th/95th percentile values rather than
        the min/max as you'd expect.  Values out of range are tied back
        to the relevant boundary.
        '''
        if not self.normalise_data:
            if self.data_order == 'DESC':
                for data in self._data:
                    if data['value'] and (isinstance(data['value'], int) or isinstance(data['value'], float)):
                        data['value'] = 10 - data['value']
                    else:
                        data['value'] = None

            self._data = self._data
            return

        # transform to postive domain 1-100
        if self._data:
            data = f_positive_1_100(self._data)
            if data:
                for value in data:
                    if value['value'] and (isinstance(value['value'], int) or isinstance(value['value'], float)):
                        value['value'] = do_skew(value['value'], self.skew)

                v_min, v_max = create_min_max(data)

                for item in data:
                    # scale to between 0 => 10
                    if item['value'] and (isinstance(item['value'], int) or isinstance(item['value'], float)):
                        value = 10.0 * (float(item['value']) - v_min) / (v_max - v_min)
                        # tie back to boundary
                        value = min(10.0, value)
                        value = max(0.0, value)

                        if self.data_order == 'DESC':
                            value = 10 - value

                        item['value'] = value

                self._data = data

    @transaction.atomic
    def save(self):

        version_obj = RiskDataSetVersion.objects.create(
            name=self.version_data['name'],
            reference=self.version_data['reference'],
            url=self.version_data['url'],
            description=self.version_data['description'],
            relates_to='C',
            file_obj=self._file,
            normalised_data=self.normalise_data
        )

        self.version_obj = version_obj

        value_objs = []

        self.error_data = []

        for data in self._data:
            try:
                exposure = fmt_4dp(data['value'])
            except:
                exposure = None

            if exposure is not None:
                if isinstance(data['id'], uuid.UUID):
                    if exposure < 0 or exposure > 10:
                        self.error_data.append({
                            'country': data['name'],
                            'score': data['value'],
                        })
                    else:
                        value_objs.append(
                            CountryRisk(
                                version=version_obj,
                                country_id=data['id'],
                                exposure=exposure,
                            )
                        )
                else:
                    countries = Country.objects.filter(name=data['name'])
                    if countries:
                        value_objs.append(
                            CountryRisk(
                                version=version_obj,
                                country_id=countries[0].id,
                            )
                        )
            else:
                countries = Country.objects.filter(name=data['name'])
                if countries:
                    value_objs.append(
                        CountryRisk(
                            version=version_obj,
                            country_id=countries[0].id,
                        )
                    )

        CountryRisk.objects.bulk_create(value_objs)


class SectorImporter(GeoExposureRawImporter):

    def read(self):
        imported_data = tablib.Dataset().load(self._file)
        for (line_no, row) in enumerate(imported_data):
            if line_no < int(self.start_row):
                logging.debug('skipping: {}'.format(row))
                continue

            if self.ignore_empty_data:
                if not row[0] and not row[2]:
                    continue

            industry = Industry.objects.filter(
                Q(slug=row[1]) | Q(name=row[1])
            )

            if industry:
                self._data.append(
                    {
                        'risk': row[0],
                        'industry': industry[0].slug,
                        'value': float(row[2]),
                        'type': row[3],
                    }
                )
            else:
                self._data.append(
                    {
                        'risk': row[0],
                        'industry': row[1],
                        'value': float(row[2]),
                        'type': row[3],
                    }
                )

    @transaction.atomic
    def save(self):
        value_objs = []
        self.version_objs = []
        self.risk_data_sets = []
        industry_data = {}
        done_industry = []

        for data in self._data:
            industry = Industry.objects.filter(
                Q(slug=data['industry']) | Q(name=data['industry'])
            )
            if industry:
                industry = industry[0]
                if industry.slug not in done_industry:
                    name = "{}_{}".format(datetime.now().strftime("%Y_%m_%d%H%M%S"), industry.slug)

                    industry_risk, _ = IndustryRiskDataSet.objects.get_or_create(industry=industry)

                    version = RiskDataSetVersion.objects.create(
                        name=name,
                        reference=self.version_data['reference'],
                        url=self.version_data['url'],
                        description=self.version_data['description'],
                        relates_to='I',
                        file_obj=self._file,
                        normalised_data=self.normalise_data
                    )
                    self.version_objs.append(version)
                    industry_risk.versions.add(version)
                    industry_risk.save()
                    done_industry.append(industry.slug)
                    self.risk_data_sets.append(str(industry_risk.id))
                    industry_data[industry.slug] = {
                        'version': version,
                        'industry': industry
                    }

        for data in self._data:
            source = RiskDataSetSource.objects.filter(name='Anthesis').first()
            if 'type' in data:
                source_type = data.get('type')
                if source_type:
                    source = RiskDataSetSource.objects.filter(name=source_type)
                    if source:
                        source = source[0]

            risk = RiskDataSet.objects.filter(
                Q(slug=data['risk']) | Q(name=data['risk'])
            )

            if risk:
                value_objs.append(
                    MaterialityRisk(
                        industry=industry_data[data['industry']]['industry'],
                        dataset_version=industry_data[data['industry']]['version'],
                        materiality=data['value'],
                        risk_factor=risk[0],
                        source=source
                    )
                )

        MaterialityRisk.objects.bulk_create(value_objs)
