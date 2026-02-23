import uuid

from company.models import CompanyAssessment
from core.models import UuidPrimaryKeyModel
from riskfactor.models import RiskDataSet

from django.db import models


class SustainableDevelopmentGoal(UuidPrimaryKeyModel):
    text = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.text


class RelatedStandard(UuidPrimaryKeyModel):
    text = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.text


class KeyPerformanceIndicator(UuidPrimaryKeyModel):
    STATUS_TYPES = (
        ("I", "In progress"),
        ("A", "Achieved"),
        ("N", "Not achieved"),
    )

    assessment = models.ForeignKey(CompanyAssessment, blank=True, null=True, on_delete=models.CASCADE)
    aspect = models.ForeignKey(RiskDataSet, on_delete=models.CASCADE)
    is_kpi = models.BooleanField(default=False)
    detail = models.TextField(blank=True, null=True)
    sdg_alignment = models.ManyToManyField(SustainableDevelopmentGoal, blank=True)
    related_standard = models.ManyToManyField(RelatedStandard, blank=True)
    status = models.CharField(
        max_length=1,
        choices=STATUS_TYPES,
        blank=True, null=True
    )
    commentary = models.TextField(blank=True, null=True)

    def related_standards_list(self):
        standards = list(self.related_standard.all().values_list('text', flat=True))
        return ', '.join(standards)

    def sdg_alignment_list(self):
        sdg = list(self.sdg_alignment.all().values_list('text', flat=True))
        return ', '.join(sdg)
