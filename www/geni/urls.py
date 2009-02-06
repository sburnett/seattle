"""
<Program Name>
  urls.py

<Started>
  October, 2008

<Author>
  ivan@cs.washington.edu
  Ivan Beschastnikh

<Purpose>
  Dispatches urls to particular view functions for GENI. Defines valid
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

# the next two lines enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
                       (r'^%s$'%(settings.URL_PREFIX), 'geni.accounts.views.login_redirect'), #'geni.accounts.views.login'), 
                       (r'^%saccounts/register$'%(settings.URL_PREFIX), 'geni.accounts.views.register',{},'register'),
                       (r'^%saccounts/login$'%(settings.URL_PREFIX), 'geni.accounts.views.login',{},'login'), 
                       (r'^%saccounts/logout$'%(settings.URL_PREFIX), 'django.contrib.auth.views.logout_then_login',{},'logout'),
                       (r'^%saccounts/help$'%(settings.URL_PREFIX), 'geni.accounts.views.help',{},'help'), 
                       
                       (r'^%scontrol/'%(settings.URL_PREFIX), include('geni.control.urls')),
                       (r'^%sdownload/'%(settings.URL_PREFIX), include('geni.download.urls')),
                       
                       # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
                       # to INSTALLED_APPS to enable admin documentation:
                       # (r'^admin/doc/', include('django.contrib.admindocs.urls')),
                       
                       # Uncomment the next line to enable the admin:
                       (r'^%sadmin/(.*)'%(settings.URL_PREFIX), admin.site.root),
                       (r'^%sadmin_media/(?P<path>.*)$'%(settings.URL_PREFIX), 'django.views.static.serve', {'document_root': settings.ADMIN_MEDIA_ROOT}),
                       (r'^%smedia/(?P<path>.*)$'%(settings.URL_PREFIX), 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),                          
)

# used in case of website work/construction
#urlpatterns = patterns('', (r'^%s*'%(settings.URL_PREFIX), 'geni.control.views.construction', {}, 'construction'))
