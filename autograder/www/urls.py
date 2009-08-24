"""
<Program Name>
  urls.py

<Started>
  January 16, 2008

<Author>
  ivan@cs.washington.edu
  Ivan Beschastnikh

<Purpose>
  Dispatches urls to particular view functions for Autograder. Defines valid
  url patterns for this application.

  This file is a URLconf (URL configuration) file for the control
  application. It defines a mapping between URLs received by the
  web-server in HTTP requests and view functions that operate on these
  requests.

  See http://docs.djangoproject.com/en/dev/topics/http/urls/?from=olddocs

  The patterns encoded below in urlpatterns are of the form:
  (regexp, view_func, args_dict, url_pattern_name) where:
  regexp:
        regular expression to matching a URL request
  view_func:
        view function called when a match is made
  args_dict:
        extra args dictionary for the view function
  url_pattern_name:
        a shorthand to refer to this pattern when buildling urls from
        templates with the url function see:
        http://docs.djangoproject.com/en/dev/topics/http/urls/?from=olddocs#id2
"""

from django.conf.urls.defaults import *
from django.conf import settings
#from user_accounts.views import hi, user_login, user_logout, user_registration, user_main, instr_request_validation
#from course.views import student_add_course, instr_create_course, view_course, view_assignment, create_assignment, create_project, view_project, instr_view_projects

urlpatterns = patterns('',
                       (r'^%stest/'%(settings.URL_PREFIX), 'autograder.upload.views.test', {}, 'test'),
                       # assignment upload view
                       (r'^%supload/'%(settings.URL_PREFIX), 'autograder.upload.views.upload', {}, 'upload'),
                       #assignment grading view
                       (r'^%sgrade/'%(settings.URL_PREFIX), 'autograder.upload.views.grade', {}, 'grade'),
                       #assignment grading stats
                       (r'^%sshowstat/'%(settings.URL_PREFIX), 'autograder.upload.views.showstat', {}, 'showstat'),
                       # see all uploaded assignments
                       (r'^%suploads/'%(settings.URL_PREFIX), 'autograder.upload.views.see_uploads', {}, 'see_uploads'),
                       
                       (r'^%sinstructor_home/'%(settings.URL_PREFIX), 'autograder.instructor.views.instructor_home', {}, 'instructor_home'),
                       (r'^%sinstructor_help/'%(settings.URL_PREFIX), 'autograder.instructor.views.instructor_help', {}, 'instructor_help'),
                       (r'^%screate_assignment/'%(settings.URL_PREFIX), 'autograder.instructor.views.create_assignment', {}, 'create_assignment'),
                       (r'^%screate_course/'%(settings.URL_PREFIX), 'autograder.instructor.views.create_course', {}, 'create_course'),
                       (r'^%sgrade_assignment/'%(settings.URL_PREFIX), 'autograder.instructor.views.grade_assignment', {}, 'grade_assignment'),
                       (r'^%sgrade_submission/'%(settings.URL_PREFIX), 'autograder.instructor.views.grade_submission', {}, 'grade_submission'),


                       (r'^%sstudent_home/'%(settings.URL_PREFIX), 'autograder.student.views.student_home', {}, 'student_home'),
                       (r'^%sstudent_help/'%(settings.URL_PREFIX), 'autograder.student.views.student_help', {}, 'student_help'),
                       (r'%sstudent_submission/'%(settings.URL_PREFIX), 'autograder.student.views.submit_assignment', {}, 'submit_assignment'),
                       (r'^%sstudent_results/'%(settings.URL_PREFIX), 'autograder.student.views.student_results', {}, 'student_results'),



                        (r'^%suser_login/'%(settings.URL_PREFIX), 'autograder.user_accounts.views.user_login', {}, 'user_login'),
                        (r'^%suser_logout/'%(settings.URL_PREFIX), 'autograder.user_accounts.views.user_logout', {}, 'user_logout'),
                        (r'^%sstudent_registration/'%(settings.URL_PREFIX), 'autograder.user_accounts.views.student_registration', {}, 'student_registration'),
                        (r'^%sinstr_registration/'%(settings.URL_PREFIX), 'autograder.user_accounts.views.instr_registration', {}, 'instr_registration'),
                        (r'^%saccounts_help/'%(settings.URL_PREFIX), 'autograder.user_accounts.views.accounts_help', {}, 'accounts_help'),
                        #(r'^%suser_homepage/'%(settings.URL_PREFIX), user_main),
                        #(r'^%srequest_validation/'%(settings.URL_PREFIX), instr_request_validation),
                        #(r'^%shi/'%(settings.URL_PREFIX), hi),
                        #(r'^%sadd_course/'%(settings.URL_PREFIX), student_add_course),
                        #(r'^%screate_course/'%(settings.URL_PREFIX), instr_create_course),
                        #(r'^%scourse/(?P<course_id>\d+)/'%(settings.URL_PREFIX), view_course),
                        #(r'^%sassignment/(?P<assignment_id>\d+)/', view_assignment),
                        #(r'^%screate_assignment/'%(settings.URL_PREFIX), create_assignment),
                        #(r'^%screate_project/'%(settings.URL_PREFIX), create_project),
                        #(r'^%sproject/(?P<project_id>\d+)/'%(settings.URL_PREFIX), view_project),
                        #(r'^%sproject_list/'%(settings.URL_PREFIX), instr_view_projects),

                      
                       
                       (r'^%spreview/(?P<classcode>\w+)/(?P<email>\w+)'%(settings.URL_PREFIX), 'autograder.upload.views.preview', {}, 'preview'),
                       (r'^%smedia/(?P<path>.*)$'%(settings.URL_PREFIX), 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),

)
