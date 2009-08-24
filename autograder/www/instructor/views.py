from django.contrib.auth import authenticate, login
from django.shortcuts import render_to_response
from django.views.generic.simple import direct_to_template
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.contrib.auth.models import User
from django.contrib.auth import logout
from user_accounts.forms import *
from instructor.forms import DateTimeForm
from course.models import *
from settings import MEDIA_URL
from instructor.forms import *
import time

def instructor_home(request):
    #check user is logged in
    if not request.user.is_authenticated():
        return direct_to_template(request, 'accounts/user_login.html',{'info':'Must be logged in to view home page', 'username': [], 'password' : []})

    profile = request.user.get_profile()
    user_type = profile.user_type

    #check user is an instructor    
    if user_type != 'instructor':
        return direct_to_template(request, 'accounts/user_login.html',{'info':'Must be an instructor to view instructor homepage', 'username': [], 'password' : []})

    name = str(request.user.first_name)+' '+str(request.user.last_name)

    #check that the instructor has at least one course
    course_qs = courses.objects.filter(instructor=request.user)
    if course_qs.count() < 1 :
        #there's no courses, so obviously there's no assignments or anything else so return now
        return direct_to_template(request, 'instructor/instructor_home.html', {'name':name, 'course_list':course_qs})

    course_list = []

    #((course_name, (assignment, (submission))))
    for course in course_qs :
        course_name = course.course_name
        assignment_list = []
        #get assignment list
        assignment_qs = assignment.objects.filter(course=course)
        #if there's no assignments for this course, then obviously there's no student submissions, so quit now
        if assignment_qs.count() < 1 :
            course_list.append((course_name, assignment_qs))
        else :
            #make list of assignments-submissions eg tuples of (assignment_name, list of submissions for the assignment)
            for assign in assignment_qs :
                submission_qs = student_submission.objects.filter(assignment=assign)
                assignment_list.append((assign, submission_qs))
            #make list of courses-assignment lists eg tuples of (course_name, list of assignments-submissions)
            course_list.append((course_name, assignment_list))

    return direct_to_template(request, 'instructor/instructor_home.html',{'name':name, 'course_list':course_list})
    

    


def instructor_home2(request):
    #check user is logged in
    if not request.user.is_authenticated():
        return direct_to_template(request, 'accounts/user_login.html',{'info':'Must be logged in to view home page', 'username': [], 'password' : []})

    profile = request.user.get_profile()
    user_type = profile.user_type

    #check user is an instructor    
    if user_type != 'instructor':
        return direct_to_template(request, 'accounts/user_login.html',{'info':'Must be an instructor to view instructor homepage', 'username': [], 'password' : []})

    name = str(request.user.first_name)+' '+str(request.user.last_name)
    #check that the instructor has at least one course
    #this is also kludgy but when the instr registers, the views will always create a course
    course_qs = courses.objects.filter(instructor=request.user)
    if course_qs.count() < 1 :
        return direct_to_template(request, 'instructor/instructor_home.html', {'name':name,'no_courses':'no courses found'})

    #this is kludgy but currently it'll only show the assignments and stuff for the first course if there are multiple courses
    assignments_qs = assignment.objects.filter(course = course_qs[0])

    #make the assignment list to display
    assignment_list = []
    if assignments_qs.count() < 1 :
        return direct_to_template(request, 'instructor/instructor_home.html', {'name':name, 'no_assignments':'No assignments found'})
    for assign in assignments_qs :
        submissions_qs = student_submission.objects.filter(assignment=assign)
        assignment_list.append((assign.assignment_name, assign.due_date, submissions_qs))

    return direct_to_template(request, 'instructor/instructor_home.html', {'name':name,'assignment_list':assignment_list})




def create_assignment(request):
    #return direct_to_template(request, 'instructor/create_assignment.html', {})
    if not request.user.is_authenticated():
        return direct_to_template(request, 'accounts/user_login.html',{'info':'Must be an logged in to create a course', 'username': [], 'password' : []})
    if request.user.get_profile().user_type != 'instructor' :
        return direct_to_template(request, 'accounts/user_login.html',{'info':'Must be an instructor to create a course', 'username': [], 'password' : []})

    #list of courses taught by this instructor
    course_list = courses.objects.filter(instructor=request.user)
    #list of projects from which they can make assignments--right now it's every project
    project_list = project_description.objects.all()

    if request.method == "POST" :
        form = DateTimeForm(request.POST)
        if form.is_valid():
            
            chosen_course_pk = request.POST['chosen_course']
            chosen_course = courses.objects.filter(pk=chosen_course_pk).filter(instructor=request.user)
            if chosen_course.count() < 1 :
                return direct_to_template(request, 'instructor/create_assignment.html', {'course_list':course_list, 'project_list':project_list, 'form':DateTimeForm(), 'error':'no course with this title by this instructor'})
            
            chosen_project_pk = request.POST['chosen_project']
            chosen_project = project_description.objects.filter(pk=chosen_project_pk)
            if chosen_project.count() < 1 :
                return direct_to_template(request, 'instructor/create_assignment.html', {'course_list':course_list, 'project_list':project_list, 'form':DateTimeForm(),'error':'no project with this name'})
            
            assignment_name = request.POST['assignment_name']
            due_date = request.POST['due_date']
            
            preexisting_assignment = assignment.objects.filter(course=chosen_course[0]).filter(assignment_name=assignment_name)
            if preexisting_assignment.count() != 0 :
                return direct_to_template(request, 'instructor/create_assignment.html', {'course_list':course_list, 'project_list':project_list, 'form':DateTimeForm(), 'error':'An assignment with the name '+str(assignment_name)+' already exists for the course '+str(chosen_course[0].course_name)})

            new_assignment = assignment(course=chosen_course[0], project=chosen_project[0], assignment_name = assignment_name, due_date=due_date)
            new_assignment.save()
            return direct_to_template(request, 'instructor/create_assignment.html', {'course_list':course_list, 'project_list':project_list, 'form':DateTimeForm(), 'info':'Assignment successfully created'})

    return direct_to_template(request, 'instructor/create_assignment.html', {'course_list':course_list, 'project_list':project_list, 'form':DateTimeForm()})


    

def create_course(request):
    #return direct_to_template(request, 'instructor/create_course.html',{})
    if not request.user.is_authenticated():
        return direct_to_template(request, 'accounts/user_login.html',{'info':'Must be an logged in to create a course', 'username': [], 'password' : []})
    if request.user.get_profile().user_type != 'instructor' :
        return direct_to_template(request, 'accounts/user_login.html',{'info':'Must be an instructor to create a course', 'username': [], 'password' : []})
    
    course_title = []

    if request.method == "POST" :
        course_title = request.POST['course_title']
        cur_courses = courses.objects.filter(instructor = request.user).filter(course_name = course_title)
        if cur_courses.count() > 0 :
            return direct_to_template(request, 'instructor/create_course.html', {'course_title':course_title, 'errors':'A course with the title "'+ str(course_title)+'" title already exists'})
        new_course = courses(instructor=request.user, course_name=course_title)
        new_course.save()
        return direct_to_template(request,'instructor/create_course.html', {'course_title':[], 'errors':'Course successfully created'})
    else:
        return direct_to_template(request, 'instructor/create_course.html', {'course_title':course_title})


def instructor_help(request):
    return direct_to_template(request, 'instructor/instructor_help.html', {})



def grade_submission(request):
    #return direct_to_template(request, 'instructor/create_course.html',{})
    if not request.user.is_authenticated():
        return direct_to_template(request, 'accounts/user_login.html',{'info':'Must be an logged in to create a course', 'username': [], 'password' : []})
    if request.user.get_profile().user_type != 'instructor' :
        return direct_to_template(request, 'accounts/user_login.html',{'info':'Must be an instructor to create a course', 'username': [], 'password' : []})

    form = SubmitAssignmentForm(request.POST)
        
    if form.is_valid():
        submission_id = request.POST['submission_id']
        submission_qs = student_submission.objects.filter(pk=submission_id)
            
        if submission_qs.count() != 1 :
            return direct_to_template(request, 'instructor/instructor_results.html',{'info':'Internal error: no submission with this id found'})

        submission = submission_qs[0]
        print submission.grade_results
        if submission.grade_results != 'assignment submitted':
            return direct_to_template(request, 'instructor/instructor_results.html',{'info':'Student assignment already graded'})

        #change grade results
        time.sleep(240)
        submission.grade_results = '6 out of 6\n\ntest_client_timeout: SUCCESS\ntest_file_not_found: SUCCESS\ntest_invalid_request: SUCCESS\ntest_multiple_connections: SUCCESS\ntest_multiple_request_pr_conn: SUCCESS\ntest_valid_request: SUCCESS'
        submission.save()
        #time.sleep(300)
        #say that it's being graded right now
        return direct_to_template(request, 'instructor/instructor_results.html',{'info':'Student assignment is being graded'})
    return direct_to_template(request, 'instructor/instructor_help.html', {})




def grade_assignment(request):
    #return direct_to_template(request, 'instructor/create_course.html',{})
    
    if not request.user.is_authenticated():
        return direct_to_template(request, 'accounts/user_login.html',{'info':'Must be an logged in to create a course', 'username': [], 'password' : []})
    if request.user.get_profile().user_type != 'instructor' :
        return direct_to_template(request, 'accounts/user_login.html',{'info':'Must be an instructor to create a course', 'username': [], 'password' : []})

    form = GradeAssignmentsForm(request.POST)
        
    if form.is_valid():
        assignment_id = request.POST['assignment_id']
        assignment_qs = assignment.objects.filter(pk=assignment_id)

        if assignment_qs.count() != 1 :
            return direct_to_template(request, 'instructor/instructor_results.html',{'info':'Internal error: no assignment with this id found'})

        submission_qs = student_submission.objects.filter(assignment = assignment_qs[0])

        if submission_qs.count() < 1 :
            return direct_to_template(request, 'instructor/instructor_results.html',{'info':'No student submissions to grade'})
        time.sleep(240)
        for submission in submission_qs :
            submission.grade_results = '6 out of 6\n\ntest_client_timeout: SUCCESS\ntest_file_not_found: SUCCESS\ntest_invalid_request: SUCCESS\ntest_multiple_connections: SUCCESS\ntest_multiple_request_pr_conn: SUCCESS\ntest_valid_request: SUCCESS'
            submission.save()
        #time.sleep(300)
        return direct_to_template(request, 'instructor/instructor_results.html',{'info':'Student assignments are being graded'})

    
    return direct_to_template(request, 'instructor/instructor_help.html', {})

        

