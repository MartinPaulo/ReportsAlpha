from django.contrib import admin
from .models import Choice, Report


# Register your models here.


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 3


class ReportAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Date information', {'fields': ['pub_date'], 'classes': ['collapse']}),
        ('Report information', {'fields': ['report_title', 'download_name', 'd3_file_name']}),
    ]
    inlines = [ChoiceInline]
    list_display = ('report_title', 'pub_date', 'was_published_recently')
    list_filter = ['pub_date']
    search_fields = ['report_title']
    ordering = ('pub_date',)


admin.site.register(Report, ReportAdmin)
