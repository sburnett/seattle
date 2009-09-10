
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.views.generic.simple import direct_to_template

def installer_creator(request):
  return direct_to_template(request, 'mainpage.html', {})

def reset_form(request):
  if not request.method == 'POST':
    return HttpResponseRedirect(reverse("installer_creator"))
  
  if request.POST['action'] == 'resetform':
    print request.POST['username']
    return HttpResponse("Done")
    
