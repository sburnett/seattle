from django.conf.urls.defaults import *
from django.conf import settings

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
                       (r'^$', 'geni.accounts.views.login'), 
                       (r'^accounts/register/$', 'geni.accounts.views.register'),
                       (r'^accounts/login/$', 'geni.accounts.views.login'), 
                       (r'^accounts/logout/$', 'django.contrib.auth.views.logout_then_login'),
                       (r'^control/', include('geni.control.urls')),
                       
                       # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
                       # to INSTALLED_APPS to enable admin documentation:
                       # (r'^admin/doc/', include('django.contrib.admindocs.urls')),
                       
                       # Uncomment the next line to enable the admin:
                       (r'^admin/(.*)', admin.site.root),
                       (r'^admin_media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': '/home/ivan/geni/admin_media/'}),
                       (r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': '/home/ivan/geni/media/'}),                          
)
