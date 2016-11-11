from django.core.mail import mail_admins
from django.shortcuts import HttpResponseRedirect
from django.shortcuts import render

from .forms import ContactForm


def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            mail_admins(
                cd['subject'],
                cd['message'])
            return HttpResponseRedirect('/')
    else:
        form = ContactForm(
            initial={'subject': 'A question'}
        )
    return render(request, 'contact/contact_form.html', {'form': form})
