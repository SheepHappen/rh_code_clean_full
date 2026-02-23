import csv
from dateutil import parser

from django.core.management.base import BaseCommand

from riskfactor.models import RiskDataSet, RiskDataSetVersion


class Command(BaseCommand):
    help = 'one time import data'

    def handle(self, *args, **options):

        with open('initial-data/versions.csv') as csv_file:
            reader = csv.reader(csv_file)
            next(reader)
            for row in reader:

                risk_version, _ = RiskDataSetVersion.objects.get_or_create(
                    created_date=parser.parse(row[0]),
                    name=row[2],
                    reference=row[3],
                    url=row[4],
                    description=row[5]
                )

                risk = RiskDataSet.objects.filter(name=row[6])

                if risk:
                    risk = risk[0]
                    if risk_version not in risk.versions.all():
                        risk.versions.add(risk_version)
                        risk.save()

        risks = RiskDataSet.objects.all()

        for risk in risks:
            versions = risk.versions.all()
            if versions and versions[0]:
                risk.active_version = versions[0]
                risk.save()
