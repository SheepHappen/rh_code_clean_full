from django.contrib import admin
from users.models import User


from .import models
from accounts.models import UserProfile
from company.models import CompanyEmailDomain


class CompanyAdmin(admin.ModelAdmin):
    class EmailDomain(admin.TabularInline):
        model = models.CompanyEmailDomain
        extra = 1
        fields = ('company', 'domain', 'enabled')

    class CompanyFund(admin.TabularInline):
        model = models.CompanyFund
        extra = 1
        fields = ('name', 'enabled')

    class InlineUser(admin.TabularInline):
        model = UserProfile
        extra = 0
        fields = (
            'user',
        )

    inlines = [
        EmailDomain,
        InlineUser,
        CompanyFund
    ]
    filter_horizontal = (
        'default_riskfactors',
        'permissions'
    )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "account_manager":
            domain = CompanyEmailDomain.objects.filter(domain='landmark.co.uk', enabled=True).first()
            users = []
            if domain and domain.company:
                profiles = UserProfile.objects.filter(company=domain.company)
                for profile in profiles:
                    users.append(profile.user.id)

            kwargs["queryset"] = User.objects.filter(id__in=users)
        return super(CompanyAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)


class IndustryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'type')
    list_filter = ("type",)


class CompanyAssessmentAdmin(admin.ModelAdmin):
    # list_display = ('report_name', 'slug', 'is_latest')
    list_display = ('report_name',)
    filter_horizontal = (
        'issues',
        'added_management_questions',
        'deleted_management_questions',
        'industries',
        'material_risks',
        'countries',
    )


class SasbCompanyLookupAdmin(admin.ModelAdmin):
    # list_display = ('report_name', 'slug', 'is_latest')
    search_fields = ("name", "industry__name")


class ManagementQuestionAnswerSetAdmin(admin.ModelAdmin):
    list_display = ('assessment', 'question')
    search_fields = ("assessment__report_name",)


admin.site.register(models.Company, CompanyAdmin)
admin.site.register(models.Industry, IndustryAdmin)
admin.site.register(models.CompanyAssessment, CompanyAssessmentAdmin)
admin.site.register(models.DocumentQuestionAnswerSet)
admin.site.register(models.ManagementQuestionAnswerSet, ManagementQuestionAnswerSetAdmin)
admin.site.register(models.AssessmentIssueRecommendations)
admin.site.register(models.IndustryType)
admin.site.register(models.SasbCompanyLookup, SasbCompanyLookupAdmin)
