from django.contrib import admin

from core import models


class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name', 'slug')


class ManagementQuestionAdmin(admin.ModelAdmin):
    filter_horizontal = ('riskfactors',)
    list_filter = ('riskfactors__name',)
    list_display = ('text', 'pdf_display_order', 'pdf_display_name')


class DocumentQuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'category', 'pdf_display_order', 'pdf_display_name', 'yes_score', 'no_score', 'is_key_policy')
    list_filter = ('category', 'is_required', 'is_best_practice', 'is_key', 'is_key_policy', 'is_market_leading', 'is_answerable')


class ThresholdAdmin(admin.ModelAdmin):
    list_display = ('text', 'lower_bound', 'upper_bound', 'colour')


class InherentRiskThresholdAdmin(admin.ModelAdmin):
    list_display = ('text', 'lower_bound', 'upper_bound', 'colour')


admin.site.register(models.Application, ApplicationAdmin)
admin.site.register(models.ManagementQuestion, ManagementQuestionAdmin)
admin.site.register(models.Permission)
admin.site.register(models.DocumentQuestion, DocumentQuestionAdmin)
admin.site.register(models.Threshold, ThresholdAdmin)
admin.site.register(models.InherentRiskThreshold, InherentRiskThresholdAdmin)
