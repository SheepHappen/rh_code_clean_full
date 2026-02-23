import csv
from dateutil import parser

from django.core.management.base import BaseCommand

from riskfactor.models import RiskDataSet, RiskFactorCategory
from core.models import Application


class Command(BaseCommand):
    help = 'one time import data'

    def handle(self, *args, **options):
        for cat in ["Economic", "Environmental", "Geopolitical", "Social", "Technological"]:
            RiskFactorCategory.objects.get_or_create(name=cat)

        for app in ["Commodity", "Value At Risk", "Sector", "Geographic"]:
            Application.objects.get_or_create(name=app)

        with open('initial-data/riskfactors.csv') as csv_file:
            reader = csv.reader(csv_file)
            next(reader)
            for row in reader:
                applications = row[0]
                category = RiskFactorCategory.objects.filter(
                    name=row[1]
                )

                if category:
                    category = category.first()
                else:
                    category = None

                risk, _ = RiskDataSet.objects.get_or_create(
                    name=row[2],
                    description=row[3],
                    recommendation=row[4],
                    reminder=row[5],
                    update_status=row[6],
                    update_due=parser.parse(row[7]),
                    category=category
                )

                for application in applications.split(','):
                    app = Application.objects.filter(name=application)
                    if app:
                        risk.applications.add(app.first())

                risk.save()

        with open('initial-data/risk-slug.csv') as csv_file:
            reader = csv.reader(csv_file)
            next(reader)
            for row in reader:
                risk = RiskDataSet.objects.filter(
                    name=row[1]
                )

                if risk:
                    risk[0].slug = row[0]
                    risk[0].save()
