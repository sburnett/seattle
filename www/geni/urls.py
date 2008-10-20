from django.conf.urls.defaults import *
from django.conf import settings

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

prefix='geni/'

urlpatterns = patterns('',
                       (r'^%s$'%(prefix), 'geni.accounts.views.login_redirect'), #'geni.accounts.views.login'), 
                       (r'^%saccounts/register$'%(prefix), 'geni.accounts.views.register',{},'register'),
                       (r'^%saccounts/login$'%(prefix), 'geni.accounts.views.login',{},'login'), 
                       (r'^%saccounts/logout$'%(prefix), 'django.contrib.auth.views.logout_then_login',{},'logout'),
                       (r'^%scontrol/'%(prefix), include('geni.control.urls')),
                       
                       # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
                       # to INSTALLED_APPS to enable admin documentation:
                       # (r'^admin/doc/', include('django.contrib.admindocs.urls')),
                       
                       # Uncomment the next line to enable the admin:
                       (r'^%sadmin/(.*)'%(prefix), admin.site.root),
                       (r'^%sadmin_media/(?P<path>.*)$'%(prefix), 'django.views.static.serve', {'document_root': '/home/ivan/geni/admin_media/'}),
                       (r'^%smedia/(?P<path>.*)$'%(prefix), 'django.views.static.serve', {'document_root': '/home/ivan/geni/media/'}),                          
)
    
