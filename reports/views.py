import logging
from wsgiref.util import FileWrapper

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.utils import timezone
from django.views import generic

from .models import Report, Choice


class IndexView(generic.ListView):
    template_name = 'reports/reports.html'
    context_object_name = 'latest_report_list'

    def get_queryset(self):
        """Return the last five published questions: excluding those published in the future."""
        return Report.objects.filter(
            pub_date__lte=timezone.now()).order_by('-pub_date')[:5]


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


class ResultsView(generic.DetailView):
    model = Report
    template_name = 'reports/results.html'


def vote(request, report_id):
    report = get_object_or_404(Report, pk=report_id)
    try:
        selected_choice = report.choice_set.get(pk=request.POST['choice'])
    except (KeyError, Choice.DoesNotExist):
        # Redisplay the question voting form.
        return render(request, 'reports/details.html', {
            'report': report,
            'error_message': "You didn't select a choice.",
        })
    else:
        selected_choice.votes += 1
        selected_choice.save()
        return HttpResponseRedirect(reverse('reports:results', args=(report.id,)))


def about(request):
    values = sorted(request.META.items())
    return render(request, 'reports/about.html', {'details': values})


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


def csv(request, report_id):
    report = get_object_or_404(Report, pk=report_id)
    duration = request.GET.get('from', '')
    download_name = report.download_name
    data_directory = '/Users/mpaulo/PycharmProjects/ReportsBeta/reports/static/fake_data/'
    try:
        logging.info(settings.STATIC_URL)
        data_directory = settings.FAKE_DATA_DIRECTORY
    except AttributeError:
        logging.warning('Fake data directory not set.')
    filename = data_directory + '%s%s' % (duration, report.download_name)
    file_extension = filename.split(".")[-1]
    # print("F %s E %s" % (filename, file_extension))
    mime_type = 'application/json' if file_extension == 'json' else 'text/csv'
    wrapper = FileWrapper(open(filename))
    response = HttpResponse(wrapper, content_type=mime_type)
    # response['Content-Length'] = os.path.getsize(filename)
    # print("S %s" % os.path.getsize(filename))
    response['Content-Disposition'] = 'attachment; filename=%s' % download_name
    return response
