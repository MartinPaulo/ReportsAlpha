from django.conf.urls import url

from . import views

app_name = 'reports'
urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='reports'),
    url(r'^csv/(?P<report_id>[0-9]+)$', views.csv, name='csv'),
    url(r'^about/$', views.about, name='about'),
    url(r'^search/$', views.search, name='search'),
    url(r'^(?P<pk>[0-9]+)/$', views.DetailView.as_view(), name='detail'),
    url(r'^(?P<pk>[0-9]+)/results/$', views.ResultsView.as_view(), name='results'),
    url(r'^(?P<report_id>[0-9]+)/vote/$', views.vote, name='vote'),
]
