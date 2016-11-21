import csv
import re
from datetime import date
from functools import wraps

import django
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
from django.apps import AppConfig
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.views import generic

from reports.graphite.capacity import fetch, GRAPHITE_JSON, GRAPHITE_CAPACITY
from .models import Report

LOGIN_URL = '/login/'
YEAR = 'year'


def _convert(name):
    """
    Converts the name parameter from CamelCase to snake case
    i.e.: CamelCase -> camel_case
    See:
    http://stackoverflow.com/questions/1175208/elegant-python-function-to-convert-camelcase-to-snake-case
    :param name: The camel case name to be converted
    :return: The input name as snake_case
    """
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


class BrowseView(LoginRequiredMixin, generic.ListView):
    login_url = '/login/'
    template_name = 'reports/reports.html'
    context_object_name = 'latest_report_list'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.selected_set = ''

    def get_queryset(self):
        """
        :return: All the published reports: excluding those published in
        the future.
        """
        reports = Report.objects.filter(pub_date__lte=timezone.now())
        self.selected_set = self.request.GET.get('set', '')
        if self.selected_set == 'cloud':
            reports = reports.filter(report_title__startswith='Cloud')
        elif self.selected_set == 'storage':
            reports = reports.filter(report_title__startswith='Storage')
        return reports.order_by('report_title')

    # we override this to add the selected set to the context
    # (is there a better way?)
    def get_context_data(self, **kwargs):
        result = super().get_context_data(**kwargs)
        result['set'] = self.selected_set
        return result


class DetailView(LoginRequiredMixin, generic.DetailView):
    login_url = LOGIN_URL
    model = Report
    template_name = 'reports/details.html'

    def get_queryset(self):
        """
        Excludes any reports that aren't published yet.
        """
        return Report.objects.filter(pub_date__lte=timezone.now())

    # we override this to add the debug flag to the context
    # (is there a better way?)
    def get_context_data(self, **kwargs):
        result = super().get_context_data(**kwargs)
        result['debug'] = settings.DEBUG
        result['set'] = self.request.GET.get('set', '')
        return result


def about(request):
    values = sorted(request.META.items())
    return render(request, 'reports/about.html',
                  {'details': values, 'debug': settings.DEBUG})


@login_required(login_url=LOGIN_URL)
def search(request):
    q = request.GET.get('q', None)
    if not q:
        errors = ['Please enter a search term!']
        return render(request, 'reports/search_form.html', {'errors': errors})
    reports = Report.objects.filter(report_title__icontains=q)
    if reports.count() > 0:
        return render(request, 'reports/search_results.html',
                      {'reports': reports, 'query': q})
    else:
        return render(request, 'reports/search_form.html', {'query': q})


def _get_start_date(duration):
    if duration == 'oneMonth':
        return date.today() - relativedelta(months=1)
    elif duration == 'threeMonths':
        return date.today() - relativedelta(months=3)
    elif duration == 'sixMonths':
        return date.today() - relativedelta(months=6)
    else:
        # duration == YEAR:
        return date.today() - relativedelta(months=12)


# from
# http://stackoverflow.com/questions/22196422/django-login-required-on-ajax-call
def xmlhttp_login_required(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated():
            raise PermissionDenied
        return view(request, *args, **kwargs)
    return wrapper


@xmlhttp_login_required
def actual(request, path):
    """
    :return: A response with the model data presented as CSV. The data is
    filtered till today by date range
    """
    duration = request.GET.get('from', YEAR)
    # we default to a date range
    date_range_desired = (_get_start_date(duration), date.today())
    on = request.GET.get('on')
    if on:
        date_desired = parse(on).date()
        date_range_desired = (date_desired, date_desired)
    desired_model = request.GET.get('model', 'unknown')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment;filename=%s.csv' % _convert(
        desired_model)
    writer = csv.writer(response)
    # if not specified 'unknown' will not be found and an error raised
    model = django.apps.apps.get_model('reports', desired_model)
    field_names = [f.name for f in model._meta.fields]
    writer.writerow(field_names)
    for instance in model.objects.filter(date__range=date_range_desired):
        writer.writerow([getattr(instance, f) for f in field_names])
    return response


@xmlhttp_login_required
def graphite(request, path):
    duration = request.GET.get('from', YEAR)
    capacity = request.GET.get('type', GRAPHITE_CAPACITY)
    desired_format = request.GET.get('format', GRAPHITE_JSON)
    graphite_response, content_type = fetch(capacity, desired_format, duration)
    response = HttpResponse(graphite_response, content_type)
    response['Content-Disposition'] = \
        'attachment; filename="capacity.%s"' % desired_format.lower()
    return response
