from .forms import ContactForm
from django.shortcuts import render
from django.shortcuts import HttpResponseRedirect
from django.core.mail import send_mail


def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            # send_mail(
            #     cd['subject'],
            #     cd['message'],
            #     cd.get('email', 'noreply@reports.org.au'),
            #     ['admin@reports.org.au'],
            # )
            return HttpResponseRedirect('/')
    else:
        form = ContactForm(
            initial={'subject': 'This is interesting!'}
        )
    return render(request, 'contact/contact_form.html', {'form': form})
