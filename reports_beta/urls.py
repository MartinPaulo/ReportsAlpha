"""reports_beta URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from .views import index

admin.site.site_header = 'ResPlat Reporting: Administration'
admin.site.site_title = 'ResPlat Reporting'

urlpatterns = [
    url('^$', index, name='index'),
    url(r'^uom_admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^reports/', include('reports.urls')),
    url(r'^uom_admin/', admin.site.urls),
    url(r'^contact/', include('contact.urls')),
    url('^', include('django.contrib.auth.urls', namespace='auth')),
    url('^registration/', include('registration.urls')),
]
