"""
<Program Name>
  urls.py

<Started>
  October, 2008

<Author>
  ivan@cs.washington.edu
  Ivan Beschastnikh

<Purpose>
  Dispatches urls to particular view functions for the download
  application. Defines valid url patterns for this application.

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
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('geni.download.views',
                       (r'^(?P<username>\w{3,32})/$', 'download', {}, 'installers'),
                       (r'^(?P<username>\w{3,32})/mac$', 'mac', {}, 'mac'),
                       (r'^(?P<username>\w{3,32})/linux$', 'linux', {}, 'linux'),
                       (r'^(?P<username>\w{3,32})/win$', 'win', {}, 'win'),
)
