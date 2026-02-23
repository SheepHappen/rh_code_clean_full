from django.contrib import admin

from country import models


class SanctionedCountryAdmin(admin.ModelAdmin):
    list_display = ('country', 'us_sanctions', 'us_sanction_comments', 'eu_sanctions', 'eu_sanction_comments')
    list_editable = ['us_sanctions', 'us_sanction_comments', 'eu_sanctions', 'eu_sanction_comments']


admin.site.register(models.SanctionedCountry, SanctionedCountryAdmin)
admin.site.register(models.Country)
