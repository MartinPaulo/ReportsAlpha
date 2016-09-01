import csv
import os
import re
from datetime import date
from json import dumps
from operator import itemgetter
from urllib.parse import urlencode
from wsgiref.util import FileWrapper

import django
import requests
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
from django.apps import AppConfig
from django.conf import settings
from django.http import HttpResponse
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views import generic

from reports.fake_data import factory
from .models import Report

first_cap_re = re.compile('(.)([A-Z][a-z]+)')
all_cap_re = re.compile('([a-z0-9])([A-Z])')


def convert(name):
    s1 = first_cap_re.sub(r'\1_\2', name)
    return all_cap_re.sub(r'\1_\2', s1).lower()


class BrowseView(generic.ListView):
    template_name = 'reports/reports.html'
    context_object_name = 'latest_report_list'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.selected_set = ''

    def get_queryset(self):
        """
        :return: The last 11 published reports: excluding those published in
        the future.
        """
        reports = Report.objects.filter(pub_date__lte=timezone.now())
        self.selected_set = self.request.GET.get('set', '')
        if self.selected_set == 'cloud':
            reports = reports.filter(report_title__startswith='Cloud')
        elif self.selected_set == 'storage':
            reports = reports.filter(report_title__startswith='Storage')
        return reports.order_by('report_title')[:11]

    # we override this to add the selected set to the context
    # (is there a better way?)
    def get_context_data(self, **kwargs):
        result = super().get_context_data(**kwargs)
        result['set'] = self.selected_set
        return result


class DetailView(generic.DetailView):
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


def data(request, path):
    duration = request.GET.get('from', '')
    data_format = request.GET.get('format', 'json')
    filename = '%s%s.%s' % (path, duration, data_format)
    file_path = os.path.join(settings.BASE_DIR, 'reports', 'static',
                             'fake_data', filename)
    mime_type = 'application/json' if data_format == 'json' else 'text/csv'
    wrapper = FileWrapper(open(file_path))
    response = HttpResponse(wrapper, content_type=mime_type)
    # response['Content-Length'] = os.path.getsize(filename)
    # print("S %s" % os.path.getsize(filename))
    response['Content-Disposition'] = 'attachment; filename=%s' % filename
    return response


def manufactured(request, path):
    duration = request.GET.get('from', 'year')
    storage_type = request.GET.get('type', 'total')
    quota = factory.get(path, duration, storage_type)
    return JsonResponse(quota, safe=False, json_dumps_params={'indent': 2})


def get_start_date(duration):
    if duration == 'oneMonth':
        return date.today() - relativedelta(months=1)
    elif duration == 'threeMonths':
        return date.today() - relativedelta(months=3)
    elif duration == 'sixMonths':
        return date.today() - relativedelta(months=6)
    else:
        # duration == 'year':
        return date.today() - relativedelta(months=12)


def actual(request, path):
    """
    :return: A response with the model data presented as CSV. The data is
    filtered till today by date range
    """
    duration = request.GET.get('from', 'year')
    # we default to a date range
    date_range_desired = (get_start_date(duration), date.today())
    on = request.GET.get('on')
    if on:
        date_desired = parse(on).date()
        date_range_desired = (date_desired, date_desired)
    desired_model = request.GET.get('model', 'unknown')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment;filename=%s.csv' % convert(
        desired_model)
    writer = csv.writer(response)
    # if not specified 'unknown' will not be found and an error raised
    model = django.apps.apps.get_model('reports', desired_model)
    field_names = [f.name for f in model._meta.fields]
    writer.writerow(field_names)
    for instance in model.objects.filter(date__range=date_range_desired):
        writer.writerow([getattr(instance, f) for f in field_names])
    return response


# Addressing the history components
# within a 2-member data-point array.
VALUE_INDEX = 0
TIMESTAMP_INDEX = 1


def _fill_nulls(data, template):
    data = dict([(timestamp, value) for value, timestamp in data])
    previous_value = 0.0
    for point in template:
        timestamp = point[TIMESTAMP_INDEX]
        value = point[VALUE_INDEX]
        if timestamp in data:
            value = data[timestamp]
        if value is None:
            yield [previous_value, timestamp]
        else:
            previous_value = value
            yield [value, timestamp]


def fill_null_datapoints(response_data):
    """Extend graphite data sets to the same length and fill in any missing
    values with either 0.0 or the previous real value that existed.
    """
    # Use the longest series as the template.  NVD3 requires that all
    # the datasets have the same data points.
    tmpl = sorted([(len(data['datapoints']), data['datapoints'])
                   for data in response_data],
                  key=itemgetter(0))[-1][1]
    tmpl = [[None, t] for v, t in tmpl]
    for data_series in response_data:
        data_points = data_series['datapoints']
        data_series['datapoints'] = list(_fill_nulls(data_points,
                                                     template=tmpl))
    return response_data


def graphite(request, path):
    args_to_call = [
        ('format', 'json'),
        ('target', "alias(cell.melbourne.capacity_768, 'QH2 and NP')"),
        ('target', "alias(cell.qh2-uom.capacity_768, 'QH2-UoM')"),
        ('from', '-3months')]
    encoded_url = "http://status1.mgmt.rc.nectar.org.au/render/?" + \
                  urlencode(args_to_call)
    response = requests.get(encoded_url)
    # TODO: should check the requests return code?
    raw = fill_null_datapoints(response.json())
    return HttpResponse(dumps(raw), response.headers['content-type'])
