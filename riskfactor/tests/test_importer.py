import os

from django.test import Client, TestCase

from riskfactor.importer import GeoExposureRawImporter
from riskfactor.tests.factories import ApplicationFactory
from pprint import pprint


class TestGeoExposureRawImporter(TestCase):
    def setUp(self):
        self.app = ApplicationFactory.create(name='geographic')

    def test_can_be_called(self):
        response = GeoExposureRawImporter()

        self.assertTrue(isinstance(response, GeoExposureRawImporter))