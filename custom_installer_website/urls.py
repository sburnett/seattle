from django.conf.urls.defaults import *
from custom_installer_website import settings

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    
    (r'^html/', include('custom_installer_website.html.urls')),
    (r'^xmlrpc', include('custom_installer_website.xmlrpc.urls')),
    
    (r'^installers/(?P<installer_id>.*)/(?P<installer_name>.*)$', 
     'custom_installer_website.common.builder.dl_installer', {}, 
     'dl_installer'),
    
    (r'^' + settings.MEDIA_URL[1:] + '(?P<path>.*)$', 'django.views.static.serve',
    {'document_root' : settings.MEDIA_ROOT}),
    
    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/(.*)', admin.site.root),
)
