from django.contrib.auth import authenticate, login
from django.shortcuts import render_to_response
from django.views.generic.simple import direct_to_template
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.contrib.auth.models import User
from django.contrib.auth import logout
from user_accounts.forms import *
from course.models import *
from settings import MEDIA_URL
from datetime import *
from student.forms import *
import os
from django.conf import settings
import sqlite3



def student_home(request):
    #check user is logged in
    if not request.user.is_authenticated():
        return direct_to_template(request, 'accounts/user_login.html',{'info':'Must be logged in to view home page', 'username': [], 'password' : []})

    name = str(request.user.first_name)+' '+str(request.user.last_name)
    profile = request.user.get_profile()
    
    #check that the student is in a course in the database
    course_qs = courses.objects.filter(pk=profile.course_id)
    if course_qs.count() != 1 :
        return direct_to_template(request, 'student/student_home.html', {'name':name,'no_courses':'not regestered for any active courses'})

    #get course name and instructor name
    course_name = course_qs[0].course_name
    instructor = course_qs[0].instructor
    instructor_name = str(instructor.first_name)+' '+str(instructor.last_name)

    #gets the assignments for the course
    assignments_qs = assignment.objects.filter(course = course_qs[0])

    #make the assignment list to display
    assignment_list = []
    if assignments_qs.count() < 1 :
        return direct_to_template(request, 'student/student_home.html', {'name':name, 'no_assignments':'No assignments found', 'course_name':course_name, 'instructor_name':instructor_name})
    
    for assign in assignments_qs :
        submission_qs = student_submission.objects.filter(assignment=assign).filter(student=request.user).order_by('-time')
        assignment_list.append((assign, submission_qs))
        
    return direct_to_template(request, 'student/student_home.html', {'name':name,'assignment_list':assignment_list, 'course_name':course_name, 'instructor_name':instructor_name})




def student_help(request):
    return direct_to_template(request, 'student/student_help.html', {})

def student_results(request):
    return direct_to_template(request, 'student/student_results.html',{})


def check_file(file):
  if ((not file.name.endswith('.zip')) and (not file.name.endswith('.tar'))): #SAL
    return "Files should be of .tar or .zip format" #SAL
  if file.size > .5*(10**6):
    return "Assignment file is too large, file size limit is .5 MB"
  return ""


    
def submit_assignment(request):
    assignment_id = ''
    submitted_file = ''
    info = ''
    
    if request.method == 'POST':
        #get the assignment id and the file
        #check that the assignment id is for a real assignment (this should be impossible for a fake id but check anyway)
        #make the file in the proper directory
        #make a new submission object for the database
        submit_time = datetime.now()
        
        form = SubmitAssignmentForm(request.POST, request.FILES)
        
        if form.is_valid():
            txt_assignment = ''
            extension = ''
            if 'student_submission' in request.FILES :
                file = request.FILES['student_submission']
                assignment_id = request.POST['assignment_id']
                info = check_file(file)
                if len(info) == 0 :
                    txt_assignment = file.read()
                    extension = file.name.split('.')[-1]
                    
                    #test assignment id is for a real assignment--should always be for a real one and the if statement should never be carried out
                    assign_qs = assignment.objects.filter(pk=assignment_id)
                    if assign_qs.count() != 1 :
                        #print out invalid assign id
                        return direct_to_template(request, 'student/student_results.html',{'info':'invalid system info, invalid assignment primary key for student submission'})

                    #test make file with assignment id, student username, and timestamp
                    if (os.path.isdir(settings.STUDENT_SUBMISSION_PATH)) == False :
                        os.mkdir(settings.STUDENT_SUBMISSION_PATH)


                    file_name =  str(request.user.username) + "_" + str(assignment_id) + "_" +str(submit_time).replace(':', '-').replace('.', '-').replace(' ','-')+ extension
                    file_path = settings.STUDENT_SUBMISSION_PATH + file_name
                    # open the file to hold the user's assignment
                    fhandle = open(file_path, 'w')

                    # save the user's assignment
                    fhandle.write(txt_assignment)
                    fhandle.close()
                    info = 'Assignment uploaded successfully.\n'


                    #save new submission info in database
                    new_submission = student_submission.objects.create(student=request.user, assignment=assign_qs[0], student_code_filename=file_name, time=submit_time, grade_results= 'assignment submitted')
                    new_submission.save()
                    print 'should be saving submission now'
                    return direct_to_template(request, 'student/student_results.html',{'info':info})

                else :
                    #somethin wrong w/ the file -- can't be saved
                    return direct_to_template(request, 'student/student_results.html',{'info':info})
            else :
                #correct file not in request.FILES---do somethin w/ this
                return direct_to_template(request, 'student/student_results.html',{'info':'Internal error: Assignment file not found in request.FILES'})
        else :
            #form is invalid -- do something with this
            return direct_to_template(request, 'student/student_results.html',{'info':'Invalid submission form'})

    return direct_to_template(request, 'student/student_results.html', {'info':'error: should only get to this via posting the student submission'})


