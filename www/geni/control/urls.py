"""
<Program Name>
  urls.py

<Started>
  October, 2008

<Author>
  ivan@cs.washington.edu
  Ivan Beschastnikh

<Purpose>
  Dispatches urls to particular view functions for control
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

urlpatterns = patterns('geni.control.views',
                       # top level urls and functions:
                       # show the user info page for this user listing the public/private keys, and user information
                       (r'^user_info$', 'user_info', {}, 'user_info'),
                       # show the current donation for this user
                       (r'^donations$', 'donations', {}, 'donations'),
                       # show the used resources page (with all the currently acquired vessels)
                       (r'^used_resources$', 'used_resources', {}, 'used_resources'),
                       # show the help page
                       (r'^help$', 'help', {}, 'help'),
                       
                       # used_resources functions:
                       # get new resources (from form)
                       (r'^get_resources$', 'get_resources', {}, 'get_resources'),
                       # delete some specific resource for this user (from form)
                       (r'^del_resource$', 'del_resource', {}, 'del_resource'),
                       # delete all resources for this user (from form)
                       (r'^del_all_resource$', 'del_all_resources', {}, 'del_all_resources'),
                       
                       # user_info functions:
                       # generate a new public/private key pair for the user (from form)
                       (r'^gen_new_key$', 'gen_new_key', {}, 'gen_new_key'),
                       # delete the user's private key from the server (from form)
                       (r'^del_priv$', 'del_priv', {}, 'del_priv'),
                       # download the user's private key (from form)
                       (r'^priv_key$', 'dl_priv_key', {}, 'priv_key'),
                       # download the user's public key (from form)
                       (r'^pub_key$', 'dl_pub_key', {}, 'pub_key'),

                       # donations functions:
                       # create a new share with another use (from form)
                       (r'^new_share$', 'new_share', {}, 'new_share'),
                       # delete an existing share with another user (from form)
                       (r'^del_share$', 'del_share', {}, 'del_share'),

                       # getdonations functions:
                       (r'^get_donations$', 'getdonations', {}, 'getdonations'),
)
