import csv

from django.core.management.base import BaseCommand

from riskfactor.models import CountryRisk, RiskDataSetVersion
from country.models import Country


class Command(BaseCommand):
    help = 'one time import data'

    def handle(self, *args, **options):

        with open('initial-data/values.csv') as csv_file:
            reader = csv.reader(csv_file)
            next(reader)
            for row in reader:
                version = RiskDataSetVersion.objects.filter(name=row[1])
                country = Country.objects.filter(name=row[2])

                if country:
                    version = RiskDataSetVersion.objects.filter(name=row[1])
                    if version:
                        risk_value, _ = CountryRisk.objects.get_or_create(
                            version=version.first(),
                            country=country.first(),
                            exposure=row[5],
                        )

        versions = RiskDataSetVersion.objects.all()

        for version in versions:
            existing_countries = [value.country.id for value in version.countryrisk_set.all()]

            if existing_countries:
                countries = Country.objects.all().exclude(id__in=existing_countries)
                value_objs = []
                for country in countries:
                    value_objs.append(
                        CountryRisk(
                            version=version,
                            country_id=country.id,
                        )
                    )

                CountryRisk.objects.bulk_create(value_objs)
