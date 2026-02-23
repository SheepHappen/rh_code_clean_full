import sys
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command

import django.apps
import subprocess

from pprint import pprint


app_list = [
    'User',
    'Country',
    'UserProfile',
    'EmailAddress',
    'EmailConfirmation',
    'ManagementQuestion',
    'DocumentQuestion',
    'Threshold',
    'SanctionedCountry',
    'RiskFactorCategory',
    'RiskDataSetSource',
    'RiskDataSetVersion',
    'CountryRisk',
    'RiskDataSet',
    'MaterialityRisk',
    'IndustryRiskDataSet',
    'Company',
    'CompanyEmailDomain',
    'Industry',
    'CompanyFund',
    'AssessmentIssueRecommendations',
    'pdfContactDetail',
    'Application',
    'DocumentQuestionAnswerSet',
    'ManagementQuestionAnswerSet',
    'CompanyAssessment'
]

class Command(BaseCommand):
    help = 'one time import data'

    def handle(self, *args, **options):
        for model in django.apps.apps.get_models():
            if model.__name__ in app_list:
                print(model.__name__)
                file_name = "fixtures/{}.json".format(model.__name__)
                app = "{}.{}".format(model._meta.app_label, model.__name__)

                sysout = sys.stdout
                sys.stdout = open(file_name, 'w')
                call_command('dumpdata', app, '--indent=4', '--natural-foreign')
                sys.stdout = sysout
