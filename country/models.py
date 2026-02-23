from core.models import UuidPrimaryKeyModel

from django.db import models


class Country(UuidPrimaryKeyModel):
    iso2 = models.CharField(
        'ISO 3166-1 Alpha 2 Name',
        max_length=2,
        unique=True
    )
    iso3 = models.CharField(
        'ISO 3166-1 Alpha 3 Name',
        max_length=3,
        unique=True
    )
    name = models.CharField(
        'Country Name',
        max_length=128,
        unique=True
    )

    def __str__(self):
        return self.name

    @property
    def abbr(self):
        return self.iso2

    class Meta:
        verbose_name = 'Country'
        verbose_name_plural = 'Countries'
        ordering = ('iso2', 'name',)


class SanctionedCountry(UuidPrimaryKeyModel):
    BOOL_CHOICES = ((True, 'Yes'), (False, 'No'))
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    us_sanctions = models.BooleanField(choices=BOOL_CHOICES)
    us_sanction_comments = models.TextField(null=True, blank=True)
    eu_sanctions = models.BooleanField(choices=BOOL_CHOICES)
    eu_sanction_comments = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.country.name
