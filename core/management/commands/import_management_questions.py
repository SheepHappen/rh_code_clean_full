import csv

from django.core.management.base import BaseCommand

from riskfactor.models import RiskDataSet
from core.models import ManagementQuestion


class Command(BaseCommand):
    help = 'one time import data'

    def handle(self, *args, **options):

        with open('initial-data/questions.csv') as csv_file:
            reader = csv.reader(csv_file)
            next(reader)
            for row in reader:

                if row[1].lower() == 'e':
                    category = 'ENVIRONMENT'
                elif row[1].lower() == 's':
                    category = 'SOCIAL'
                else:
                    category = 'GOVERNANCE'

                question, _ = ManagementQuestion.objects.get_or_create(
                    category=category,
                    text=row[2],
                )

                for risk in row[0].split(','):
                    risk = RiskDataSet.objects.filter(name=risk.strip())
                    if risk:
                        question.riskfactors.add(risk.first())

                question.save()
