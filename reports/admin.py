from django.contrib import admin

from .models import Report


# Register your models here.

class ReportAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Date information', {'fields': ['pub_date'], }),
        ('Report information', {'fields': ['report_title', 'description', 'd3_file_name']}),
    ]
    list_display = ('report_title', 'pub_date', 'was_published_recently')
    list_filter = ['pub_date']
    search_fields = ['report_title']
    ordering = ('pub_date',)


admin.site.register(Report, ReportAdmin)
