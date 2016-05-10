from django.shortcuts import render
import datetime


def index(request):
    current_date = datetime.datetime.now()
    return render(request, 'index.html', locals())
