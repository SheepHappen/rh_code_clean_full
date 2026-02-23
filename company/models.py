from datetime import datetime

from django.core.validators import EmailValidator
from django.core.exceptions import ValidationError
from django_extensions.db.fields import AutoSlugField
from django.db import models

from users.models import User
from core.models import DocumentQuestion, ManagementQuestion, UuidPrimaryKeyModel
from country.models import Country
from riskfactor.models import RiskDataSet


class Company(UuidPrimaryKeyModel):
    USER_SIGNUP = (
        ("X", "Not allowed - new employees can only be added in the company admin area"),
        ("A", "Allowed - employees can register, but must be accepted by an admin"),
    )

    name = models.CharField(
        max_length=40,
        unique=True,
        verbose_name='organisation name'
    )
    organisation_type = models.CharField(max_length=40)
    country = models.ForeignKey(
        Country,
        null=True,
        blank=True,
        verbose_name='Country',
        on_delete=models.SET_NULL
    )
    address = models.TextField('address')
    phone = models.CharField('phone', max_length=40)
    primary_contact = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL
    )
    sector = models.CharField('sector', max_length=40, blank=True)
    city = models.CharField('city', max_length=40, blank=True)
    post_code = models.CharField('post code', max_length=10, blank=True)
    default_riskfactors = models.ManyToManyField(
        'riskfactor.RiskDataSet',
        blank=True,
        verbose_name="Default Selected Riskfactors",
        help_text="To have only a subset of riskfactors initially \"checked\" "
                  "in an assessment, select them here.<br/>"
                  "Leave none (or all of them) selected to have "
                  "them all checked<br/>"
    )
    user_signup = models.CharField(
        max_length=1,
        choices=USER_SIGNUP,
        default="A",
        verbose_name="User sign-up configuration"
    )
    reference = models.CharField('Company reference', max_length=255)
    account_manager = models.ForeignKey(User, null=True, blank=True, related_name="account_manager", on_delete=models.SET_NULL)
    permissions = models.ManyToManyField('core.Permission', blank=True)

    class Meta:
        verbose_name_plural = 'companies'

    def __str__(self):
        return u'{}'.format(self.name)


class CompanyEmailDomain(UuidPrimaryKeyModel):
    def validate_domain(value):
        if not EmailValidator.domain_regex.match(value):
            raise ValidationError("{} is not a valid email domain.".format(value))

    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    domain = models.CharField(max_length=63, validators=[validate_domain], unique=True)
    enabled = models.BooleanField(blank=True, default=True)

    def __str__(self):
        return self.domain


class IndustryType(UuidPrimaryKeyModel):
    name = models.CharField(max_length=255, unique=True, verbose_name='Type')
    icon = models.CharField(max_length=255, blank=True, null=True)
    slug = AutoSlugField(max_length=255, editable=False, populate_from=["name"])

    class Meta:
        ordering = ("name", )

    def __str__(self):
        return self.name


class Industry(UuidPrimaryKeyModel):
    name = models.CharField(max_length=255, unique=True, verbose_name='Industry Name')
    slug = AutoSlugField(max_length=255, editable=False, populate_from=["name"])
    description = models.TextField(blank=True, null=True, verbose_name='Insight paragraph')
    short_description = models.TextField(blank=True, null=True, verbose_name='Description')
    type = models.ForeignKey(IndustryType, blank=True, null=True, on_delete=models.CASCADE)

    class Meta:
        ordering = ("name", )

    def __str__(self):
        return self.name


class CompanyFund(UuidPrimaryKeyModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    slug = AutoSlugField(max_length=255, editable=False, populate_from=["name"])
    enabled = models.BooleanField(blank=True, default=True)

    class Meta:
        ordering = ("name", )
        unique_together = ("company", "name")

    def __str__(self):
        return self.name


class SasbCompanyLookup(UuidPrimaryKeyModel):
    name = models.CharField(max_length=255, verbose_name='organisation name')
    industry = models.ForeignKey(Industry, on_delete=models.CASCADE)

    class Meta:
        ordering = ("industry", )

    def __str__(self):
        return u'{} - {}'.format(self.name, self.industry.name)


class CompanyAssessment(UuidPrimaryKeyModel):
    STATUS = (
        ("C", "Completed"),
        ("I", "Incomplete"),
        ("W", "Waiting for report"),
    )
    DEAL_TYPES = (
        ("T", "Target Company"),
        ("N", "Not Acquired"),
        ("P", "Portfolio Company"),
        ("E", "Exited"),
    )
    report_name = models.CharField(max_length=255, unique=True, verbose_name="Report Name")
    slug = AutoSlugField(
        max_length=255,
        editable=False,
        populate_from=["report_name"],
        verbose_name='Assessment Code'
    )
    date_created = models.DateTimeField(editable=False, auto_now_add=True)
    date_updated = models.DateTimeField(editable=True, auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=1, choices=STATUS, default="I")
    deal_type = models.CharField(max_length=1, choices=DEAL_TYPES, default="N")
    company_name = models.CharField(max_length=255, verbose_name="Company Name")
    company_fund = models.ForeignKey(
        CompanyFund,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='funds'
    )
    company_headquarters = models.CharField(max_length=255, null=True, blank=True, verbose_name="Headquarters")
    company_employee_count = models.PositiveIntegerField(null=True, blank=True, verbose_name="Number of employees")
    client_reference = models.CharField(max_length=255, blank=True)
    report_reference = models.CharField(max_length=255, verbose_name="Report reference", blank=True)
    website = models.URLField(null=True, blank=True)
    company_description = models.TextField(max_length=270, null=True, blank=True)
    industries = models.ManyToManyField(Industry, blank=True)
    material_risks = models.ManyToManyField(RiskDataSet, blank=True, related_name='risks')
    countries = models.ManyToManyField(Country, blank=True, related_name='countries')
    risk_summary = models.TextField(null=True, blank=True)
    issues = models.ManyToManyField(RiskDataSet, blank=True, related_name='issues')
    issue_extra_title = models.CharField(max_length=255, null=True, blank=True)
    issue_extra_description = models.TextField(null=True, blank=True)
    references = models.TextField(null=True, blank=True)
    added_management_questions = models.ManyToManyField(ManagementQuestion, blank=True, related_name='added_management_questions')
    deleted_management_questions = models.ManyToManyField(ManagementQuestion, blank=True, related_name='deleted_management_questions')
    is_latest = models.BooleanField(blank=True, default=True)
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL)
    answered_optional = models.BooleanField(blank=True, default=False)
    custom_risk_score = models.ForeignKey('core.Threshold', null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.report_name

    def get_mananagement_question_answer(self, question):
        return ManagementQuestionAnswerSet.objects.filter(
            assessment=self,
            question=question
        ).first()

    def get_management_questions_based_on_risk(self, company, category=None):
        """
        Filter questions seen by the user based on the risk(category).
        As well as this exclude questions that have been removed.
        """
        questions = []
        company_questions = list(
            self.deleted_management_questions.all().values_list('id', flat=True)
        ) + list(self.added_management_questions.all().values_list('id', flat=True))

        for material_risk in self.material_risks.all().order_by('name'):
            if category:
                query_set = material_risk.questions.filter(
                    category=category,
                    company__isnull=True
                ).exclude(id__in=company_questions)
            else:
                query_set = material_risk.questions.filter(company__isnull=True).exclude(id__in=company_questions)

            for question in query_set:
                if question in self.deleted_management_questions.all():
                    continue
                questions.append(question)

        return list(set(questions))

    def get_pdf_management_questions(self, company, risks):
        """
        Get the management questions that will be displayed on the pdf, including the answer.
        """
        questions = []
        for risk in risks:
            try:
                query_set = ManagementQuestion.objects.filter(
                    riskfactors__id=risk.obj_id,
                    pdf_display_order__isnull=False
                ).order_by('pdf_display_order')
            except:
                query_set = ManagementQuestion.objects.filter(
                    riskfactors__id=risk,
                    pdf_display_order__isnull=False
                ).order_by('pdf_display_order')

            for question in query_set:
                answer = self.get_mananagement_question_answer(question)
                if answer:
                    question.answer = answer.answer
                    question.insufficient = answer.insufficient
                    question.priority = answer.priority
                else:
                    question.answer = None
                    question.insufficient = 'YES'
                    question.priority = 'NO'
                questions.append(question)

        return list(set(questions))

    def get_company_questions(self, company, exclude_list, category=None):
        questions = ManagementQuestion.objects.filter(
            company=company,
        ).exclude(id__in=exclude_list)
        filtered_list = []
        risk_list = list(self.material_risks.all().values_list('name', flat=True).order_by('name'))

        if category:
            questions = questions.filter(category=category)

        for question in questions:
            if question in self.deleted_management_questions.all():
                continue

            question_risk_list = list(question.riskfactors.all().values_list('name', flat=True))

            if any(x in question_risk_list for x in risk_list):
                filtered_list.append(question)

        if category:
            for question in self.added_management_questions.filter(category=category):
                filtered_list.append(question)
        else:
            for question in self.added_management_questions.all():
                filtered_list.append(question)

        return list(set(filtered_list))

    def get_category_questions(self, company, category=None, risk_slugs=None, required_only=False):
        questions = self.get_management_questions_based_on_risk(company, category)
        question_ids = [question.id for question in questions]
        questions = questions + self.get_company_questions(company, question_ids, category)

        required_questions = []
        optional_questions = []

        for question in questions:
            answer = self.get_mananagement_question_answer(question)
            question_risks = list(question.riskfactors.values_list('slug', flat=True))

            if answer:
                question.answer = answer.answer
                question.insufficient = answer.insufficient
                question.priority = answer.priority
            else:
                question.answer = None
                question.insufficient = None
                question.priority = None

            if risk_slugs and any(elem in question_risks for elem in risk_slugs):
                question.hightlight = True
                required_questions.append(question)
            else:
                question.hightlight = False
                optional_questions.append(question)

        if required_only:
            return required_questions, question_ids
        else:
            return required_questions + optional_questions, question_ids

    def save(self, *args, **kwargs):
        self.date_updated = datetime.now()
        super(CompanyAssessment, self).save(*args, **kwargs)


class DocumentQuestionAnswerSet(UuidPrimaryKeyModel):
    ANSWERS = (
        ("Y", "Yes"),
        ("N", "No"),
        ("X", "No Evidence"),
    )
    assessment = models.ForeignKey(CompanyAssessment, on_delete=models.CASCADE)
    question = models.ForeignKey(DocumentQuestion, on_delete=models.CASCADE)
    answer = models.CharField(
        max_length=1,
        choices=ANSWERS,
        default="N",
    )
    notes = models.CharField(max_length=200, null=True, blank=True)

    class Meta:
        unique_together = ('assessment', 'question')


class ManagementQuestionAnswerSet(UuidPrimaryKeyModel):
    assessment = models.ForeignKey(CompanyAssessment, on_delete=models.CASCADE)
    question = models.ForeignKey(ManagementQuestion, on_delete=models.CASCADE)
    answer = models.TextField(null=True, blank=True)
    insufficient = models.BooleanField(default=False)
    priority = models.BooleanField(default=False)

    class Meta:
        unique_together = ('assessment', 'question')


class AssessmentIssueRecommendations(UuidPrimaryKeyModel):
    assessment = models.ForeignKey(CompanyAssessment, on_delete=models.CASCADE)
    issue = models.CharField(max_length=255)
    recommendation = models.TextField()

    def __str__(self):
        return "assessment: {}, issue: {}".format(self.assessment.id, self.issue)
