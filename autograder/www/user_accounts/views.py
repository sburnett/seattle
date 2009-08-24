from django.contrib.auth import authenticate, login
from django.shortcuts import render_to_response
from django.views.generic.simple import direct_to_template
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.contrib.auth.models import User
from django.contrib.auth import logout
from user_accounts.forms import *
from course.models import *
from settings import MEDIA_URL, URL_PREFIX
from instructor.views import instructor_home
from student.views import student_home

def hi(request):
    
    return render_to_response('hi.html',{'results':User.objects.all()})

def accounts_help(request):
    return direct_to_template(request, 'accounts/accounts_help.html', {'info':''})

def user_login(request):
    info = ""
    username = []
    password = []
    if request.method == "POST" :
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                # Redirect to a success page.
                if(request.user.get_profile().user_type == 'instructor'):
                    #return HttpResponseRedirect('../instructor_home/')
                    #return direct_to_template(request, '/instructor_home.html',
                    return instructor_home(request)
                else :
                    return student_home(request)            
            else:
                # Return a 'disabled account' error message
                return direct_to_template(request, 'accounts/user_login.html', {'info':'This account has been disabled.--provide registration page link', 'username': username, 'password' : password})
        # Return an 'invalid login' error message.
        return direct_to_template(request, 'accounts/user_login.html', {'info' : 'Invalid login information.', 'username': [], 'password' : []})
    else:
        return direct_to_template(request, 'accounts/user_login.html', {'info' : info, 'username': username, 'password' : password})




def user_logout(request):
    logout(request)
    #return render_to_response('user_logout.html')
    return direct_to_template(request, 'accounts/user_login.html', {'info' : 'Successfully logged out', 'username': [], 'password' : []})




def student_registration(request):
    info=''
    if request.method == 'POST':
        
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            #check instr last name and course id match
            if User.objects.filter(last_name = request.POST['instructor_name']).count() < 1 :
                return direct_to_template(request, 'accounts/student_registration.html', {'info':'No instructor with the last name "'+ str(request.POST['instructor_name'])+'" exists', 'form':StudentRegistrationForm(), 'MEDIA_URL':MEDIA_URL})
            possible_courses = courses.objects.filter(pk = request.POST['course_id'])
            if possible_courses.count() != 1 :
                return direct_to_template(request, 'accounts/student_registration.html', {'info':'No course with the code "'+ str(request.POST['course_id'])+'" exists', 'form':StudentRegistrationForm(), 'MEDIA_URL':MEDIA_URL})
            instr_name = possible_courses[0].instructor.last_name
            if instr_name != request.POST['instructor_name'] :
                return direct_to_template(request, 'accounts/student_registration.html', {'info':'The course with course code '+str(request.POST['course_id'])+' is not taught by '+str(request.POST['instructor_name']), 'form':StudentRegistrationForm(), 'MEDIA_URL':MEDIA_URL})
            new_user = form.save()
            #log the new user in so you can go to user homepage without having to have the user manually login directly after registering
            new_user = authenticate(username=request.POST['username'], password=request.POST['password1'])
            login(request, new_user)
            return student_home(request)
    else:
        form = StudentRegistrationForm()
    return direct_to_template(request, 'accounts/student_registration.html', {'info':info, 'form':form, 'MEDIA_URL':MEDIA_URL})


def instr_registration(request):
    info=''
    if request.method == 'POST':
        form = InstructorRegistrationForm(request.POST)
        if form.is_valid():
            new_user = form.save()
            #log the new user in so you can go to user homepage without having to have the user manually login directly after registering
            new_user = authenticate(username=request.POST['username'], password=request.POST['password1'])
            login(request, new_user)
            return instructor_home(request)
    else:
        form = InstructorRegistrationForm()

    #return render_to_response('register.html', {'MEDIA_URL':MEDIA_URL, 'form':form,})
    return direct_to_template(request, 'accounts/instr_registration.html', {'info':info, 'form':form, 'MEDIA_URL':MEDIA_URL})





def instr_request_validation(request):
    
    website = []
    
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/user_login')
    if request.user.get_profile().user_type != 'instructor' :
        return HttpResponse('Only instructors can be validated.')
    if request.user.get_profile().is_validated == 'False' :
        return render_to_response('request_validation.html',{'website':website, 'comments':'You have already been validated'})
    
    prior_requests = pending_validations.objects.filter(user=request.user)
    if prior_requests.count() != 0 :
        return render_to_response('request_validation.html', {'website':website, 'comments':'Your previous validation request has yet to be processed.  Please check again later.'})
    
    if request.method == "POST" :
        website = request.POST['website']
        validation = pending_validations(user=request.user, website=website)
        validation.save()
        return render_to_response('request_validation.html',{'website':website, 'comments':'validation request is pending'})          
    return render_to_response('request_validation.html',{'website':website})


