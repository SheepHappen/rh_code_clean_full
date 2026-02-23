import csv
from datetime import datetime
import os

from django.core.management.base import BaseCommand

from core.settings import BASE_DIR
from company.models import Industry
from riskfactor.models import RiskDataSet, IndustryRiskDataSet, MaterialityRisk, RiskDataSetSource, RiskDataSetVersion


# def create_missing_risk_industry_data(version, industry):
#     existing_risks = [value.risk_factor.id for value in version.materialityrisk_set.all()]
#     if existing_risks:
#         risks = RiskDataSet.objects.all().exclude(id__in=existing_risks)
#         value_objs = []
#         for risk in risks:
#             value_objs.append(
#                 MaterialityRisk(
#                     dataset_version=version,
#                     industry=industry,
#                     risk_factor=risk
#                 )
#             )

#         MaterialityRisk.objects.bulk_create(value_objs)


class Command(BaseCommand):
    def handle(self, *args, **options):
        with open('initial-data/industries.csv') as csv_file:
            reader = csv.reader(csv_file)
            next(reader)

            for row in reader:
                industry, _ = Industry.objects.get_or_create(
                    name=row[2]
                )
                industry.slug = row[1]
                industry.save()

        url = '/initial-data/industry_scores'

        files = [i for i in os.listdir(BASE_DIR + url)]
        data = {}

        source, _ = RiskDataSetSource.objects.get_or_create(
            name='SASB',
            colour='green'
        )
        for input_file in files:
            inner_list = []
            industry = None
            with open(os.path.join(BASE_DIR + url, input_file)) as csv_file:
                reader = csv.reader(csv_file)
                next(reader)
                for row in reader:
                    industry = row[4]
                    industry = Industry.objects.filter(slug=row[4])
                    if industry:
                        inner_list.append({
                            'risk': row[0],
                            'score': row[8],
                        })
            if industry:
                data[industry[0].name] = inner_list

        industries = data.keys()

        for industry in industries:
            industry_str = industry
            industry = Industry.objects.filter(name=industry_str)
            industry = industry[0]
            version_name = "{}_{}".format(datetime.now().strftime("%Y_%m_%d"), industry.slug)
            version, _ = RiskDataSetVersion.objects.get_or_create(
                name=version_name,
                relates_to='I'
            )
            data_set, _ = IndustryRiskDataSet.objects.get_or_create(
                industry=industry
            )

            data_set.dataset_version = version
            data_set.save()

            for item in data[industry_str]:
                risk = RiskDataSet.objects.filter(slug=item['risk'])
                if risk:
                    MaterialityRisk.objects.get_or_create(
                        industry=industry,
                        dataset_version=version,
                        materiality=item['score'],
                        risk_factor=risk[0],
                        source=source
                    )
            # create_missing_risk_industry_data(version, industry)
