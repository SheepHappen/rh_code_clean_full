import os

from datetime import datetime

from django.db import models
from users.models import User
from django_extensions.db.fields import AutoSlugField

from country.models import Country

from core.models import Application, UuidPrimaryKeyModel


class RiskFactorCategory(UuidPrimaryKeyModel):
    name = models.CharField(max_length=255, unique=True, verbose_name='Category Name')
    slug = AutoSlugField(max_length=255, editable=False, populate_from=["name"], verbose_name='Category Code')
    sort_order = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        verbose_name = "Risk Factor Category"
        verbose_name_plural = "Risk Factor Categories"
        ordering = ('name',)

    def __str__(self):
        return self.name


class RiskDataSetSource(UuidPrimaryKeyModel):
    name = models.CharField(max_length=255, unique=True, verbose_name='Source')
    slug = AutoSlugField(max_length=255, editable=False, populate_from=["name"])
    colour = models.CharField(max_length=6, unique=True)

    class Meta:
        ordering = ("name", )

    def __str__(self):
        return self.name


class RiskDataSetVersion(UuidPrimaryKeyModel):
    RELATION = (
        ("C", "Country"),
        ("I", "Industry"),
    )
    created_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Creation Date',
        editable=False
    )
    name = models.CharField(max_length=255, verbose_name='Risk Factor Version')
    reference = models.TextField(null=True, blank=True)
    url = models.CharField(max_length=1024, verbose_name='URL', null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    relates_to = models.CharField(max_length=1, choices=RELATION, default="C")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    file_obj = models.FileField(upload_to='uploads/version_data/')
    skew = models.CharField(max_length=255, blank=True, null=True)
    data_order = models.CharField(max_length=255, blank=True, null=True)
    normalised_data = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Risk Factor Version"
        ordering = ('-created_date',)

    def filename(self):
        return os.path.basename(self.file_obj.name)

    def __str__(self):
        return self.name


class CountryRisk(UuidPrimaryKeyModel):
    version = models.ForeignKey(RiskDataSetVersion, on_delete=models.CASCADE)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    exposure = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = "Exposure Score"


class RiskDataSet(UuidPrimaryKeyModel):
    UPDATE_STATUS = (
        ('o', "Up to date"),
        ('r', "Update required"),
        ('p', "Update pending"),
    )

    name = models.CharField(max_length=255, unique=True, verbose_name='Risk Factor Name')
    slug = AutoSlugField(max_length=255, editable=False, populate_from=["name"], verbose_name='Risk Factor Code')
    created_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Creation Date',
        editable=False
    )
    description = models.TextField(verbose_name='Description', blank=True)
    pdf_description = models.TextField(verbose_name='Pdf Description', blank=True)
    recommendation = models.TextField(blank=True, verbose_name='Default recommendation',)
    abbreviated_recommendation = models.TextField(blank=True)
    reminder = models.BooleanField(default=True, blank=True)
    update_status = models.CharField(max_length=1, choices=UPDATE_STATUS, default="o")
    update_due = models.DateField()
    notes = models.TextField(null=True, blank=True)
    active_version = models.ForeignKey(
        RiskDataSetVersion,
        on_delete=models.SET_NULL,
        verbose_name='Active version',
        null=True,
        blank=True,
        limit_choices_to={"relates_to": "C"}
    )
    versions = models.ManyToManyField(RiskDataSetVersion, related_name='versions', limit_choices_to={"relates_to": "C"})
    applications = models.ManyToManyField(Application, related_name='riskfactors')
    category = models.ForeignKey(RiskFactorCategory, on_delete=models.CASCADE, verbose_name='Category')

    class Meta:
        verbose_name = "Risk Factor"
        ordering = ('name',)

    def __str__(self):
        return self.name

    def calculate_update_status(self):
        todays_date = datetime.today().date()
        if not self.active_version and todays_date > self.update_due:
            return 'p'
        elif todays_date > self.update_due:
            return 'r'
        elif todays_date < self.update_due:
            return 'o'
        elif todays_date == self.update_due:
            return 'r'
        else:
            return 'o'

    def save(self, *args, **kwargs):
        self.update_status = self.calculate_update_status()
        super(RiskDataSet, self).save(*args, **kwargs)


class MaterialityRisk(UuidPrimaryKeyModel):
    industry = models.ForeignKey("company.Industry", on_delete=models.CASCADE)
    risk_factor = models.ForeignKey("RiskDataSet", on_delete=models.CASCADE, null=True, blank=True)
    dataset_version = models.ForeignKey(RiskDataSetVersion, on_delete=models.CASCADE, limit_choices_to={"relates_to": "I"})
    materiality = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True
    )
    source = models.ForeignKey(RiskDataSetSource, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        verbose_name = "Materiality Score"


class IndustryRiskDataSet(UuidPrimaryKeyModel):
    industry = models.ForeignKey(
        "company.Industry",
        on_delete=models.CASCADE,
    )
    dataset_version = models.ForeignKey(
        RiskDataSetVersion,
        on_delete=models.CASCADE,
        limit_choices_to={"relates_to": "I"},
        null=True,
        blank=True
    )
    versions = models.ManyToManyField(
        RiskDataSetVersion,
        related_name='industry_versions',
        limit_choices_to={"relates_to": "I"},
    )

    def __str__(self):
        return self.industry.name
