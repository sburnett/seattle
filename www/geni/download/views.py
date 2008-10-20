from django.views.generic.simple import direct_to_template

def download(request,username):
    return direct_to_template(request,'download/installers.html', {'username' : username})
