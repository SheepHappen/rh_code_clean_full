import sys
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command

from users.models import User

import django.apps
import subprocess

from pprint import pprint

import_list = [
    "fixtures/Application.json",
    "fixtures/User.json",
    "fixtures/Country.json",
    "fixtures/SanctionedCountry.json",
    "fixtures/Company.json",
    "fixtures/CompanyEmailDomain.json",
    "fixtures/CompanyFund.json",
    "fixtures/UserProfile.json",
    "fixtures/EmailAddress.json",
    "fixtures/Threshold.json",
    "fixtures/Industry.json",
    "fixtures/pdfContactDetail.json",
    "fixtures/RiskDataSetVersion.json",
    "fixtures/RiskDataSetSource.json",
    "fixtures/RiskFactorCategory.json",
    "fixtures/RiskDataSet.json",
    "fixtures/IndustryRiskDataSet.json",
    "fixtures/CountryRisk.json",
    "fixtures/MaterialityRisk.json",
    "fixtures/DocumentQuestion.json",
    "fixtures/ManagementQuestion.json",
    "fixtures/CompanyAssessment.json",
    "fixtures/DocumentQuestionAnswerSet.json",
    "fixtures/ManagementQuestionAnswerSet.json",
    "fixtures/AssessmentIssueRecommendations.json",
]  

class Command(BaseCommand):
    help = 'one time import data'

    def handle(self, *args, **options):
       
        for i in import_list:
            print(i)
            call_command('loaddata', i)

        users = User.objects.all()

        for u in users:
            u.save()