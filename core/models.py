import uuid
from django.db import models
from django_extensions.db.fields import AutoSlugField

from core.constants import ENUM_RPT_QUESTION_CATEGORY


class UuidPrimaryKeyModel(models.Model):
    id = models.UUIDField(primary_key=True, unique=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class Application(UuidPrimaryKeyModel):
    name = models.CharField(max_length=255, unique=True)
    slug = AutoSlugField(max_length=255, editable=False, populate_from=["name"])

    def __str__(self):
        return self.name


class ManagementQuestion(UuidPrimaryKeyModel):
    category = models.CharField(max_length=32, choices=ENUM_RPT_QUESTION_CATEGORY)
    text = models.TextField()
    company = models.ForeignKey("company.Company", null=True, blank=True, on_delete=models.SET_NULL)
    riskfactors = models.ManyToManyField("riskfactor.RiskDataSet", related_name='questions')
    pdf_display_order = models.PositiveIntegerField(null=True, blank=True)
    pdf_display_name = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.text


class DocumentQuestion(UuidPrimaryKeyModel):
    category = models.CharField(max_length=32, choices=ENUM_RPT_QUESTION_CATEGORY)
    text = models.TextField()
    company = models.ForeignKey("company.Company", null=True, blank=True, on_delete=models.SET_NULL)
    trigger_question = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL)
    yes_score = models.PositiveIntegerField(default=1, null=True, blank=True)
    no_score = models.PositiveIntegerField(default=0, null=True, blank=True)
    is_answerable = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)
    pdf_display_order = models.PositiveIntegerField(null=True, blank=True)
    pdf_display_name = models.CharField(max_length=255, null=True, blank=True)
    is_key = models.BooleanField(default=False)
    is_key_policy = models.BooleanField(default=False)
    is_best_practice = models.BooleanField(default=False)
    is_market_leading = models.BooleanField(default=False)
    is_required = models.BooleanField(default=False)

    @property
    def is_key_question(self):
        return self.is_key or self.is_best_practice or self.is_market_leading

    @property
    def answer_text(self):
        return 'Y' if self.yes_score else 'N'

    def __str__(self):
        return self.text


class Threshold(UuidPrimaryKeyModel):
    text = models.CharField(max_length=255, unique=True)
    lower_bound = models.DecimalField(default=0, max_digits=3, decimal_places=1)
    upper_bound = models.DecimalField(default=0, max_digits=3, decimal_places=1)
    colour = models.CharField(max_length=255, null=True, blank=True)
    text_in_sentence = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.text


# Legacy, im not sure this is being used anymore.
class InherentRiskThreshold(UuidPrimaryKeyModel):
    text = models.CharField(max_length=255, unique=True)
    lower_bound = models.DecimalField(default=0, max_digits=3, decimal_places=1)
    upper_bound = models.DecimalField(default=0, max_digits=3, decimal_places=1)
    colour = models.CharField(max_length=255, null=True, blank=True)
    text_in_sentence = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.text


class Permission(UuidPrimaryKeyModel):
    name = models.CharField(max_length=255)
    endpoint = models.CharField(null=True, blank=True, max_length=255)

    def __str__(self):
        if self.endpoint:
            return "{} - {}".format(self.name, self.endpoint)
        else:
            return self.name
