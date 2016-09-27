from django.conf.urls import url

from . import views

app_name = 'reports'
urlpatterns = [
    url(r'^$', views.BrowseView.as_view(), name='reports'),
    url(r'^graphite/(.*)', views.graphite, name='graphite'),
    url(r'^actual/(.*)', views.actual, name='actual'),
    url(r'^about/$', views.about, name='about'),
    url(r'^search/$', views.search, name='search'),
    url(r'^(?P<pk>[0-9]+)/$', views.DetailView.as_view(), name='detail'),
]

