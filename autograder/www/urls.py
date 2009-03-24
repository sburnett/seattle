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
                       (r'^%spreview/(?P<classcode>\w+)/(?P<email>\w+)'%(settings.URL_PREFIX), 'autograder.upload.views.preview', {}, 'preview'),
                       (r'^%smedia/(?P<path>.*)$'%(settings.URL_PREFIX), 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),

)
