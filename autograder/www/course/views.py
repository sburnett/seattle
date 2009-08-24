from django.contrib.auth import authenticate, login
from django.shortcuts import render_to_response
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.contrib.auth.models import User
from course.models import *
import sqlite3
from django.db.models import Q
from course.forms import *
import os
import glob
from django.conf import settings


DATABASE_NAME = '/Users/jenn/Desktop/ag/autograder/database.db'


def create_assignment(request):
    #check that the user is signed in and an instructor
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/user_login')
    if request.user.get_profile().user_type != 'instructor' :
        return HttpResponse('Only instructors can create courses.')

    course_title = []
    assignment_name = []
    project_name = []
    student_viewable = []
      
    if request.method == 'POST':

      print request.POST
      
      course_title = request.POST['course_title']
      assignment_name = request.POST['assignment_name']
      project_name = request.POST['project_name']
      student_viewable = request.POST['student_viewable']

      check_course = courses.objects.filter(instructor=request.user).filter(course_name=course_title)

      if check_course.count() != 1 :
        return render_to_response('create_assignment.html', {'comments':'No course with the name '+str(course_title)+' exists', 'course_title':course_title, 'assignment_name':assignment_name, 'project_name':project_name, 'student_viewable':'False'})

      check_project = project_description.objects.filter(name=project_name)

      if check_project.count() != 1:
        return render_to_response('create_assignment.html', {'comments':'No project with the name "'+str(project_name)+'" exists', 'course_title':course_title, 'assignment_name':assignment_name, 'project_name':project_name, 'student_viewable':'False'})
      
      desired_course = courses.objects.get(instructor=request.user, course_name=course_title)
      desired_project = project_description.objects.get(name=project_name)

      new_assignment = assignment(course=desired_course, project=desired_project, student_results_viewable=student_viewable, assignment_name=assignment_name)
      new_assignment.save()
      return render_to_response('create_assignment.html', {'comments':'Assignment successfully created', 'course_title':[], 'assignment_name':[], 'project_name':[], 'student_viewable':'False'})
      
    return render_to_response('create_assignment.html', {'course_title':course_title, 'assignment_name':assignment_name, 'project_name':project_name, 'student_viewable':'False'})


def check_file(file):
  if ((not file.name.endswith('.zip')) and (not file.name.endswith('.tar'))): #SAL
    return "Files should be of .tar or .zip format" #SAL
  if file.size > .5*(10**6):
    return "Project is too large, file size limit is .5 MB"
  return ""



#def project_upload(request):
def create_project(request):

    #check that the user is signed in and an instructor
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/user_login')
    if request.user.get_profile().user_type != 'instructor' :
        return HttpResponse('Only instructors can create courses.')
      
    info = ''

    # check if the user submitted the UploadProjectForm
    if request.method == 'POST':
        form = UploadProjectForm(request.POST, request.FILES)
        # check validity of the form
        if form.is_valid():
            txt_project = ""
            extension = "" #SAL
            if 'test_code' in request.FILES :
                file = request.FILES['test_code']
                info = check_file(file)
                if len(info) == 0:                 
             
                  txt_project = file.read()

                  extension = file.name.split('.')[-1]
                  project_name = str(form.cleaned_data['name'])
                  sharable = form.cleaned_data['sharable']
                  description = str(form.cleaned_data['description'])
                  
                  #check if root directory for project uploads exists
                  if (os.path.isdir(settings.PROJECT_UPLOAD_PATH))==False:
                     os.mkdir(settings.PROJECT_UPLOAD_PATH)

                  file_path = settings.PROJECT_UPLOAD_PATH + project_name.replace(' ','_') + "_." + extension

                  #check if the file already exists (eg someone already picked this name)
                  if os.path.isfile(file_path) == True:
                      return render_to_response('create_project.html',{'info':'The project name "'+project_name+'" is already taken.', 'form':UploadProjectForm()})

                  # open the file to hold the user's project
                  fhandle = open(file_path, 'w')

                  # save the user's assignment
                  fhandle.write(txt_project)
                  fhandle.close()
                  info = 'Project uploaded successfully.\n'
                  info += 'File: '+ file_path.split('/')[-1]

                  new_project = project_description(name = project_name, sharable = sharable, description = description, test_code_filename = str(file_path), created_by = request.user)
                  new_project.save()

                  return render_to_response('create_project.html',{'info':'Project successfully created.', 'form':UploadProjectForm()})
                  
                  #if 'nohtml' not in request.POST:
                    #return direct_to_template(request, 'upload/success_upload.html', {'info' : info, 'form' : forms.UploadProjectForm()})
                    #return render_to_response('create_project.html', {})
                    #return HttpResponse('project created successfully')

        else:
            info = 'Form is invalid'
            pass
            
    if 'nohtml' in request.POST:
       return HttpResponse(info)
      
    form = UploadProjectForm() 
    return render_to_response('create_project.html', {'info' : info, 'form' : form})




def view_project(request, project_id):
    
    #check that the user is signed in and an instructor
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/user_login')
    if request.user.get_profile().user_type != 'instructor' :
        return HttpResponse('Only instructors can create courses.')
    
    #check that the project with the corresponding primary key exists
    check_project = project_description.objects.filter(pk=int(project_id))
    if check_project.count() != 1 :
        error = 'No project with the id '+ str(project_id) + ' exists'
        return render_to_response('view_project.html', {'errors':error})
    #ok it exists and the user is an instructor so show the list
    return render_to_response('view_project.html', {'project':project_description.objects.get(pk=int(project_id))})
    



#def create_project(request):
#    return HttpResponse('need to implement create project')



def instr_view_projects(request):
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/user_login')
    if request.user.get_profile().user_type != 'instructor' :
        return HttpResponse('Only instructors can create courses.')
    projects = project_description.objects.filter(Q(created_by=request.user) | Q(sharable = 'True'))
    return render_to_response('view_project_list.html', {'project_list':projects})
    


#list the assignments for this course
def view_course(request, course_id):
    check_course = courses.objects.filter(pk=int(course_id))
    if check_course.count() == 0 :
        return HttpResponse('Invalid course id')
    course = courses.objects.get(pk=int(course_id))
    #get assignment list
    assignment_list = assignment.objects.filter(course = course)
    print assignment_list
    #see if it's the instructor or student viewing the page
    if request.user != course.instructor :
        return render_to_response('course_homepage.html', {'assignment_list':assignment_list, 'name':course.course_name, 'instructor':course.instructor.username})
    return render_to_response('course_homepage.html',{'assignment_list':assignment_list, 'name':course.course_name})



def view_assignment(request, assignment_id):
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/user_login')
    
    #send to instr or student html page
    if request.user.get_profile().user_type != 'instructor' :
        return render_to_response('instr_view_assignment.html')
      
    return render_to_response('student_view_assignment.html')



def student_add_course(request):
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/user_login')
    
    course_title = []
    instructor_name = []
    course_id = []

    if request.method == "POST" :
        course_title = request.POST['course_title']
        instructor_name = request.POST['instructor_name']
        course_id = request.POST['course_id']

        if course_id != None and course_id != "":
            #check if id is in system
            desired_course = courses.objects.filter(pk = course_id)
            if desired_course.count() != 1 :
                return render_to_response('add_course.html', {'course_title':course_title, 'instructor_name':instructor_name, 'course_id':course_id, 'error': 'No course id matching '+str(course_id)+' was found'})

            #the course_id matches a course id in the system so check if there is a preexisting connection between the user and this course
            desired_course = courses.objects.get(pk = course_id)
            check_student_conn = course_roster.objects.filter(student=request.user).filter(course=desired_course)
            if check_student_conn.count() != 0 :
                return render_to_response('add_course.html', {'course_title':course_title, 'instructor_name':instructor_name, 'course_id':course_id, 'error': 'You have already added this course'})
            #the course exists and the student hasn't already added it, so add it            
            updated_roster = course_roster(student=request.user, course=desired_course)
            updated_roster.save()
            return render_to_response('add_course.html', {'course_title':course_title, 'instructor_name':instructor_name, 'course_id':course_id, 'error': 'course successfully added'})
        
        elif instructor_name != "" and course_title != "" :

            conn = sqlite3.connect(DATABASE_NAME)
            cursor = conn.cursor()

            query_stmnt = "SELECT course_courses.id FROM auth_user, course_courses WHERE auth_user.username = '"+ instructor_name +"' AND auth_user.id = course_courses.instructor_id AND course_courses.course_name = '"+course_title+"'"
            cursor.execute(query_stmnt)
            results = cursor.fetchall()
            cursor.close()

            if len(results) < 1 or len(results[0]) != 1 :
                return render_to_response('add_course.html', {'course_title':course_title, 'instructor_name':instructor_name, 'course_id':course_id, 'error': 'No matching instructor and course title combination was found'})

            #ok so the course exists, now check if the student has already added it
            course = courses.objects.get(pk = results[0][0])
            check_student_conn = course_roster.objects.filter(student=request.user).filter(course=course)
            if check_student_conn.count() != 0 :
                return render_to_response('add_course.html', {'course_title':course_title, 'instructor_name':instructor_name, 'course_id':course_id, 'error': 'You have already added this course'})

            #the course exists and the student hasn't already added it, so add it            
            updated_roster = course_roster(student=request.user, course= course)
            updated_roster.save()
            return render_to_response('add_course.html', {'course_title':course_title, 'instructor_name':instructor_name, 'course_id':course_id, 'error': 'course successfully added'})

        
        else:

            return render_to_response('add_course.html', {'course_title':course_title, 'instructor_name':instructor_name, 'course_id':course_id, 'error': 'Information invalid or improperly filled out.'})
   
    return render_to_response('add_course.html',{'course_title':course_title, 'instructor_name':instructor_name, 'course_id':course_id})



def instr_create_course(request):
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/user_login')
    if request.user.get_profile().user_type != 'instructor' :
        return HttpResponse('Only instructors can create courses.')
    
    course_title = []

    if request.method == "POST" :
        course_title = request.POST['course_title']
        cur_courses = courses.objects.filter(instructor = request.user).filter(course_name = course_title)
        if cur_courses.count() > 0 :
            return render_to_response('create_course.html', {'course_title':course_title, 'errors':'A course with the title "'+ str(course_title)+'" title already exists'})
        new_course = courses(instructor=request.user, course_name=course_title)
        new_course.save()
        return render_to_response('create_course.html', {'course_title':course_title, 'errors':'course successfully added'})
    else:
        return render_to_response('create_course.html', {'course_title':course_title})


