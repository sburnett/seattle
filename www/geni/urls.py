"""
<Program Name>
  urls.py

<Started>
  October, 2008

<Author>
  ivan@cs.washington.edu
  Ivan Beschastnikh

<Purpose>
  Dispatches urls to particular view functions for the geni
  application.

<Usage>
  For more information on url dispatching in django see:
  http://docs.djangoproject.com/en/dev/topics/http/urls/
"""

from django.conf.urls.defaults import *
from django.conf import settings

# the next two lines enable the admin:
from django.contrib import admin
admin.autodiscover()

# this is our global url prefix that must match what Apache uses for
# django's geni application (see /etc/apache2/apache2.conf)
prefix='geni/'

urlpatterns = patterns('',
                       (r'^%s$'%(prefix), 'geni.accounts.views.login_redirect'), #'geni.accounts.views.login'), 
                       (r'^%saccounts/register$'%(prefix), 'geni.accounts.views.register',{},'register'),
                       (r'^%saccounts/login$'%(prefix), 'geni.accounts.views.login',{},'login'), 
                       (r'^%saccounts/logout$'%(prefix), 'django.contrib.auth.views.logout_then_login',{},'logout'),
                       
                       (r'^%scontrol/'%(prefix), include('geni.control.urls')),
                       (r'^%sdownload/'%(prefix), include('geni.download.urls')),
                       
                       # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
                       # to INSTALLED_APPS to enable admin documentation:
                       # (r'^admin/doc/', include('django.contrib.admindocs.urls')),
                       
                       # Uncomment the next line to enable the admin:
                       (r'^%sadmin/(.*)'%(prefix), admin.site.root),
                       (r'^%sadmin_media/(?P<path>.*)$'%(prefix), 'django.views.static.serve', {'document_root': '/home/ivan/geni/admin_media/'}),
                       (r'^%smedia/(?P<path>.*)$'%(prefix), 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),                          
)
