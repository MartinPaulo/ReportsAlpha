import datetime
from django.db import models
from django.utils import timezone


# super user: mpaulo password: /stupidDjango


class Report(models.Model):
    report_title = models.CharField(max_length=100)
    pub_date = models.DateTimeField('date published')
    download_name = models.CharField(max_length=100, default='report.csv')
    d3_file_name = models.CharField(max_length=100, default='new_users.js')

    def __str__(self):
        return self.report_title

    def was_published_recently(self):
        """
        Return True if was published in the last day, False otherwise

        >>> import datetime
        >>> from django.utils import timezone
        >>> from reports.models import Report
        >>> future_report = Report(pub_date=timezone.now()+ datetime.timedelta(days=30), report_title="Futurama")
        >>> future_report.was_published_recently()
        False
        """
        now = timezone.now()
        return now - datetime.timedelta(days=1) <= self.pub_date <= now
    was_published_recently.admin_order_field = 'pub_date'
    was_published_recently.boolean = True
    was_published_recently.short_description = 'Published recently?'


class Choice(models.Model):
    question = models.ForeignKey(Report, on_delete=models.CASCADE)
    choice_text = models.CharField(max_length=200)
    votes = models.IntegerField(default=0)

    def __str__(self):
        return self.choice_text
