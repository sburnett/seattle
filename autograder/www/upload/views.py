"""
<Program Name>
  views.py

<Started>
  January 16, 2008

<Author>
  ivan@cs.washington.edu
  Ivan Beschastnikh

<Purpose>
  Defines view functions that handle HTTP requests

  This file contains view functions for the control application which
  are called whenever a url is matched in autograder.urls. These
  functions always take an HTTP request object, and return an HTTP
  response object, which is sometimes generated automatically by
  referencing a template via direct_to_template() and other
  django shorthands.

  For more information on views in django see:
  See http://docs.djangoproject.com/en/dev/topics/http/views/

  Multiple functions in this file contain the @login_required()
  decorator which enforces the HTTP connection to the browser to have
  a valid cookie that was established at login time:
  http://docs.djangoproject.com/en/dev/topics/auth/#the-login-required-decorator
"""

from django.views.generic.simple import direct_to_template
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.conf import settings
import glob
import os

# import local forms used by the upload application
import forms

def check_file(file):
  if ((not file.name.endswith('.zip')) and (not file.name.endswith('.tar'))): #SAL
    return "Files should be of .tar or .zip format" #SAL
  if file.size > .5*(10**6):
    return "Assignment file is too large, file size limit is .5 MB"
  return ""

def upload(request):
    """
    <Purpose>
        Constructs the upload of assignment form for a student

    <Arguments>
        request:
            An HTTP request object            

    <Exceptions>
        None

    <Side Effects>
        Uploads the file to the local file system if the user submits
        the upload form.

    <Returns>
        An HTTP response object that represents the upload page on succes.
    """

    info = ''

    # check if the user submitted the UploadAssignmentForm
    if request.method == 'POST':
        form = forms.UploadAssignmentForm(request.POST, request.FILES)
        # check validity of the form
        if form.is_valid():
            txt_assignment = ""
            extension = "" #SAL
            if 'assignment' in request.FILES:
                file = request.FILES['assignment']
                info = check_file(file)
                if len(info) == 0:                 
             
                  txt_assignment = file.read()

                  extension = file.name.split('.')[-1] #SAL            
                  # extract the user's classcode and email from the submitted form
                  classcode = str(form.cleaned_data['class_code'])
                  email = str(form.cleaned_data['email'])

                  #check if root directory for assignemnt uploads exists
                  if (os.path.isdir(settings.ASSIGNMENT_UPLOAD_PATH))==False:
                     os.mkdir(settings.ASSIGNMENT_UPLOAD_PATH)

                  file_path = settings.ASSIGNMENT_UPLOAD_PATH + classcode + "_" + email + "_." + extension

                  # open the file to hold the user's assignment
                  fhandle = open(file_path, 'w')

                  # save the user's assignment
                  fhandle.write(txt_assignment)
                  fhandle.close()
                  info = 'Assignment uploaded successfully.\n'
                  info += 'File: '+ file_path.split('/')[-1]

                  if (os.path.isdir(settings.ASSIGNMENT_UPLOAD_PATH+"Status"))==False:
                    os.mkdir(settings.ASSIGNMENT_UPLOAD_PATH+"Status")

                  os.system('echo "Not Graded\n" >>'+settings.ASSIGNMENT_UPLOAD_PATH+"Status/"+file_path.split('/')[-1]+".txt; chmod 664 "+settings.ASSIGNMENT_UPLOAD_PATH+"Status/"+file_path.split('/')[-1]+".txt")
                    #Status folder should exist
                  
                  if 'nohtml' not in request.POST:
                    return direct_to_template(request, 'upload/success_upload.html',
                              {'info' : info, 'form' : forms.UploadAssignmentForm()})

        else:
            info = 'Form is invalid'
            pass
            
    if 'nohtml' in request.POST:
       return HttpResponse(info)
     
    return direct_to_template(request, 'upload/upload.html',
                              {'info' : info, 'form' : forms.UploadAssignmentForm()})

def showstat(request):
  
  if request.method == 'POST':
    file=request.POST['which']
    form = forms.UploadAssignmentForm(request.POST)

    status="No Status Available"
    if os.path.exists(settings.ASSIGNMENT_UPLOAD_PATH+"Status/"+file+".txt"):
      status=open(settings.ASSIGNMENT_UPLOAD_PATH+"Status/"+file+".txt").read()
    return direct_to_template(request, 'upload/default.html',
                {'info' : status, 'form' : forms.UploadAssignmentForm()})

#    return HttpResponse(status)



def grade(request):
  whichFile=""
  result=""
  if request.method == 'POST':
    form = forms.UploadAssignmentForm(request.POST)
    whichFile=request.POST['which']


    if (os.path.exists(settings.ASSIGNMENT_UPLOAD_PATH+"ToGrade/"+whichFile)):
       return direct_to_template(request, 'upload/default.html',
                {'info' : whichFile+" is scheduled for grading (being graded) already", 'form' : forms.UploadAssignmentForm()})

    if (os.path.isdir(settings.ASSIGNMENT_UPLOAD_PATH+"ToGrade"))==False:
      os.mkdir(settings.ASSIGNMENT_UPLOAD_PATH+"ToGrade")
    os.system('cp '+settings.ASSIGNMENT_UPLOAD_PATH+whichFile+' '+settings.ASSIGNMENT_UPLOAD_PATH+"ToGrade; chmod 664 "+settings.ASSIGNMENT_UPLOAD_PATH+"ToGrade/"+whichFile)

#    for hidden in form.hidden_fields:
 #      result+=hidden
    
#    if form.is_valid():

#    whichFile = str(form.cleaned_data['which'])
#  email = str(form.cleaned_data['email'])
  #return HttpResponse("Grading"+whichFile+result)
  return direct_to_template(request, 'upload/default.html',
                {'info' : "Grading "+whichFile, 'form' : forms.UploadAssignmentForm()})
    
def see_uploads(request):
    """
    <Purpose>
        Shows the user a table of all the assignment uploads

    <Arguments>
        request:
            An HTTP request object            

    <Exceptions>
        None

    <Side Effects>
        None

    <Returns>
        An HTTP response object that represents the current uploads
    """

    uploaded_files = glob.glob(settings.ASSIGNMENT_UPLOAD_PATH + "*")

    upload_entries = []
    for file in uploaded_files:
      #if we have a file(assinment)
      if os.path.isdir(file)==False:
        file = file.split(settings.ASSIGNMENT_UPLOAD_PATH)[1]
        
        classcode, email = file.split('_.')[0].split("_")

        status="No Status Available"
        if os.path.exists(settings.ASSIGNMENT_UPLOAD_PATH+"Status/"+file+".txt"):
           status=open(settings.ASSIGNMENT_UPLOAD_PATH+"Status/"+file+".txt").next()
        upload_entries.append((classcode, email, file, status))
        
    return direct_to_template(request, 'upload/uploads.html', {'upload_entries' : upload_entries})

def preview(request, classcode, email):
    return direct_to_template(request, 'upload/uploads.html', {'upload_entries' : upload_entries})

def test(request):
    upload_entries = []
    upload_entries.append(("TEST"))
    return direct_to_template(request,'upload/profile.html', {'upload_entries' : upload_entries})
