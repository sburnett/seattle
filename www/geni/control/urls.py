"""
<Program Name>
  models.py

<Started>
  October, 2008

<Author>
  ivan@cs.washington.edu
  Ivan Beschastnikh

<Purpose>
  Defines valid url patterns for the control application

  This file is a URLconf (URL configuration) file for the control
  application. It defines a mapping between URLs received by the
  web-server in HTTP requests and view functions that operate on these
  requests.

  See http://docs.djangoproject.com/en/dev/topics/http/urls/?from=olddocs
"""

from django.conf.urls.defaults import *
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('geni.control.views',
                       # the patterns below are of the form:
                       # (regexp, view_func, args_dict, url_pattern_name)
                       # where:
                       # regexp -- regular expression to matching a URL request
                       # view_func -- view function called when a match is made
                       # args_dict -- extra args dictionary for the view function
                       # url_pattern_name -- a shorthand to refer to
                       # this pattern when buildling urls from
                       # templates with url function (see
                       # http://docs.djangoproject.com/en/dev/topics/http/urls/?from=olddocs#id2 )
                       
                       # top level urls and functions:
                       (r'^user_info$', 'user_info', {}, 'user_info'),
                       (r'^donations$', 'donations', {}, 'donations'),
                       (r'^used_resources$', 'used_resources', {}, 'used_resources'),
                       
                       # used_resources functions:
                       (r'^get_resources$', 'get_resources', {}, 'get_resources'),
                       (r'^del_resource$', 'del_resource', {}, 'del_resource'),
                       (r'^del_all_resource$', 'del_all_resources', {}, 'del_all_resources'),
                       
                       # user_info functions:
                       (r'^gen_new_key$', 'gen_new_key', {}, 'gen_new_key'),
                       (r'^del_priv$', 'del_priv', {}, 'del_priv'),
                       (r'^priv_key$', 'dl_priv_key', {}, 'priv_key'),
                       (r'^pub_key$', 'dl_pub_key', {}, 'pub_key'),

                       # donations functions
                       (r'^new_share$', 'new_share', {}, 'new_share'),
                       (r'^del_share$', 'del_share', {}, 'del_share'),
)
