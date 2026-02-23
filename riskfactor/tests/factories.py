import random
import decimal

import factory

from core.models import Application
from country.models import Country


class CountryFactory(factory.DjangoModelFactory):
    class Meta:
        model = Country

    iso2 = factory.Sequence(lambda n: 'iso2%d' % n)
    iso3 = factory.Sequence(lambda n: 'iso3%d' % n)
    name = factory.Sequence(lambda n: 'name%d' % n)


class ApplicationFactory(factory.DjangoModelFactory):
    class Meta:
        model = Application

    slug = factory.Sequence(lambda n: 'slug%d' % n)
    name = factory.Sequence(lambda n: 'name%d' % n)