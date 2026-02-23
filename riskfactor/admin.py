from django.contrib import admin

from riskfactor import models


class RiskFactorCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name', 'slug')


class RiskDataSetVersionAdmin(admin.ModelAdmin):
    list_display = ('name', 'url')
    search_fields = ('name', 'url')


class CountryRiskAdmin(admin.ModelAdmin):
    list_display = ('version', 'country', 'exposure')
    search_fields = ('version', 'country', 'exposure')


class RiskDataSetAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name', 'slug')

    filter_horizontal = (
        'applications',
        'versions'
    )


class MaterialityRiskAdmin(admin.ModelAdmin):
    list_display = ('industry', 'risk_factor', 'materiality')
    search_fields = ('industry__name',)


admin.site.register(models.RiskFactorCategory, RiskFactorCategoryAdmin)
admin.site.register(models.RiskDataSetVersion, RiskDataSetVersionAdmin)
admin.site.register(models.CountryRisk, CountryRiskAdmin)
admin.site.register(models.IndustryRiskDataSet)
admin.site.register(models.RiskDataSet, RiskDataSetAdmin)
admin.site.register(models.MaterialityRisk, MaterialityRiskAdmin)
admin.site.register(models.RiskDataSetSource)
