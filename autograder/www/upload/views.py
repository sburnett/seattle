from django.views.generic.simple import direct_to_template
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.conf import settings
import forms

UPLOAD_PATH = '/tmp/uploads/'

def upload(request):
    info = ''
    if request.method == 'POST':
        form = forms.UploadAssignmentForm(request.POST, request.FILES)
        if form.is_valid():
            txt_assignment = ""
            if 'assignment' in request.FILES:
                file = request.FILES['assignment']
                if file.size > .5*(10**6):
                    return HttpResponse("Assignment file is too large, file size limit is .5 MB")
                txt_assignment = file.read()
            # this saves the user's record to the database
            f = open(UPLOAD_PATH + '%s_%s'%(form.cleaned_data['class_code'], form.cleaned_data['email']), 'w')
            f.write(txt_assignment)
            f.close()
            info = 'Assignment uploaded successfully.'
            
    return direct_to_template(request, 'upload/upload.html', {'info' : info, 'form' : forms.UploadAssignmentForm()})
    


