import logging
import os
from wsgiref.util import FileWrapper

from django.conf import settings
from django.http import HttpResponse
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views import generic

from reports.fake_data import factory
from .models import Report


class IndexView(generic.ListView):
    template_name = 'reports/reports.html'
    context_object_name = 'latest_report_list'

    def get_queryset(self):
        """Return the last 11 published reports: excluding those published in the future."""
        return Report.objects.filter(
            pub_date__lte=timezone.now()).order_by('-pub_date')[:11]


class DetailView(generic.DetailView):
    model = Report
    template_name = 'reports/details.html'

    def get_queryset(self):
        """
        Excludes any reports that aren't published yet.
        """
        return Report.objects.filter(pub_date__lte=timezone.now())

    # we override this to add the debug flag to the context (is there a better way?)
    def get_context_data(self, **kwargs):
        result = super().get_context_data(**kwargs)
        result['debug'] = settings.DEBUG
        return result


def about(request):
    values = sorted(request.META.items())
    return render(request, 'reports/about.html', {'details': values, 'debug': settings.DEBUG})


def search(request):
    q = request.GET.get('q', None)
    if not q:
        errors = ['Please enter a search term!']
        return render(request, 'reports/search_form.html', {'errors': errors})
    reports = Report.objects.filter(report_title__icontains=q)
    if reports.count() > 0:
        return render(request, 'reports/search_results.html', {'reports': reports, 'query': q})
    else:
        return render(request, 'reports/search_form.html', {'query': q})


def data(request, path):
    duration = request.GET.get('from', '')
    data_format = request.GET.get('format', 'json')
    filename = '%s%s.%s' % (path, duration, data_format)
    file_path = os.path.join(settings.BASE_DIR, 'reports', 'static', 'fake_data', filename)
    mime_type = 'application/json' if data_format == 'json' else 'text/csv'
    wrapper = FileWrapper(open(file_path))
    response = HttpResponse(wrapper, content_type=mime_type)
    # response['Content-Length'] = os.path.getsize(filename)
    # print("S %s" % os.path.getsize(filename))
    download_name = 'data'
    response['Content-Disposition'] = 'attachment; filename=%s' % download_name
    return response


def manufactured(request, path):
    duration = request.GET.get('from', 'year')
    storage_type = request.GET.get('type', 'total')
    quota = factory.get(path, duration, storage_type)
    return JsonResponse(quota, safe=False, json_dumps_params={'indent': 2})
