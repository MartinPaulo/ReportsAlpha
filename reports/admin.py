import logging

from django.conf import settings
from django.contrib import admin
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.mail import EmailMessage

from .models import Report, BroadcastEmail

logger = logging.getLogger("reports")


class ReportAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Date information', {'fields': ['pub_date'], }),
        ('Report information',
         {'fields': ['report_title', 'description', 'd3_file_name',
                     'related']}),
    ]
    list_display = ('report_title', 'pub_date', 'was_published_recently')
    list_filter = ['pub_date']
    search_fields = ['report_title']
    ordering = ('pub_date',)


admin.site.register(Report, ReportAdmin)


class BroadcastEmailAdmin(admin.ModelAdmin):
    """
    Uses django actions to send emails to all users.
    If the number of users grows we should consider using celery to send the
    emails.
    """
    model = BroadcastEmail

    def submit_email(self, request, queryset):
        try:
            admins_emails = [a[1] for a in settings.ADMINS if a[1]]
            users_emails = [user.email for user in User.objects.all() if
                            user.email and user.email not in admins_emails]
            for email in queryset:
                EmailMessage(
                    email.subject,
                    email.message,
                    from_email=settings.SERVER_EMAIL,
                    to=admins_emails,
                    bcc=users_emails
                ).send()
        except Exception as err:
            logger.exception("Error on broadcast email")
            self.message_user(request, err, level=messages.ERROR)

    submit_email.short_description = 'Broadcast selected Email(s)'
    submit_email.allow_tags = True

    actions = [submit_email]
    list_display = ("subject", "created")
    search_fields = ['subject', ]


admin.site.register(BroadcastEmail, BroadcastEmailAdmin)
