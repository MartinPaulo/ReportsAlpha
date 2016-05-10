import datetime
import doctest

from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils import timezone

from reports import models
from .models import Report


# Create your tests here.

class ReportMethodTests(TestCase):
    def test_was_published_recently_with_future_question(self):
        """
        was_published_recently() should return False for questions whose pub_date is in the future
        """
        time = timezone.now() + datetime.timedelta(days=30)
        future_report = Report(pub_date=time, report_title='Test Report')
        self.assertEqual(future_report.was_published_recently(), False)

    def test_was_published_recently_with_old_question(self):
        """
        was_published_recently() should return False for questions whose
        pub_date is older than 1 day.
        """
        time = timezone.now() - datetime.timedelta(days=30)
        old_question = Report(pub_date=time)
        self.assertEqual(old_question.was_published_recently(), False)

    def test_was_published_recently_with_recent_question(self):
        """
        was_published_recently() should return True for questions whose
        pub_date is within the last day.
        """
        time = timezone.now() - datetime.timedelta(hours=1)
        recent_question = Report(pub_date=time)
        self.assertEqual(recent_question.was_published_recently(), True)


def create_report(report_title, days):
    """
    Creates a Report with the given `report_title` and published the
    given number of `days` offset to now (negative for Reports published
    in the past, positive for Reports that have yet to be published).
    """
    time = timezone.now() + datetime.timedelta(days=days)
    return Report.objects.create(report_title=report_title,
                                 pub_date=time)


class ReportViewTests(TestCase):
    def test_index_view_with_no_reports(self):
        """
        If no reports exist, an appropriate message should be displayed.
        """
        response = self.client.get(reverse('reports:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No reports are available.")
        self.assertQuerysetEqual(response.context['latest_report_list'], [])

    def test_index_view_with_a_past_question(self):
        """
        reports with a pub_date in the past should be displayed on the
        index page.
        """
        create_report(report_title="Past report.", days=-30)
        response = self.client.get(reverse('reports:index'))
        self.assertQuerysetEqual(
            response.context['latest_report_list'],
            ['<Report: Past report.>']
        )

    def test_index_view_with_a_future_report(self):
        """
        reports with a pub_date in the future should not be displayed on
        the index page.
        """
        create_report(report_title="Future report.", days=30)
        response = self.client.get(reverse('reports:index'))
        self.assertContains(response, "No reports are available.",
                            status_code=200)
        self.assertQuerysetEqual(response.context['latest_report_list'], [])

    def test_index_view_with_future_report_and_past_report(self):
        """
        Even if both past and future reports exist, only past reports
        should be displayed.
        """
        create_report(report_title="Past report.", days=-30)
        create_report(report_title="Future report.", days=30)
        response = self.client.get(reverse('reports:index'))
        self.assertQuerysetEqual(
            response.context['latest_report_list'],
            ['<Report: Past report.>']
        )

    def test_index_view_with_two_past_reports(self):
        """
        The reports index page may display multiple reports.
        """
        create_report(report_title="Past report 1.", days=-30)
        create_report(report_title="Past report 2.", days=-5)
        response = self.client.get(reverse('reports:index'))
        self.assertQuerysetEqual(
            response.context['latest_report_list'],
            ['<Report: Past report 2.>', '<Report: Past report 1.>']
        )


class ReportIndexDetailTests(TestCase):
    def test_detail_view_with_a_future_report(self):
        """
        The detail view of a report with a pub_date in the future should
        return a 404 not found.
        """
        future_report = create_report(report_title='Future report.',
                                      days=5)
        response = self.client.get(reverse('reports:detail',
                                           args=(future_report.id,)))
        self.assertEqual(response.status_code, 404)

    def test_detail_view_with_a_past_report(self):
        """
        The detail view of a report with a pub_date in the past should
        display the reports's text.
        """
        past_report = create_report(report_title='Past report.',
                                    days=-5)
        response = self.client.get(reverse('reports:detail',
                                           args=(past_report.id,)))
        self.assertContains(response, past_report.report_title,
                            status_code=200)


def load_tests(loader, tests, ignore):
    # http://stackoverflow.com/questions/2380527/django-doctests-in-views-py
    tests.addTests(doctest.DocTestSuite(models))
    return tests
