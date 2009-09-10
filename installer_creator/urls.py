from django.conf.urls.defaults import *
from installer_creator import settings

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    
    (r'^html/', include('installer_creator.html.urls')),
    (r'^xmlrpc', include('installer_creator.xmlrpc.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/(.*)', admin.site.root),
)

# If DEBUG is True, then this is for development rather than production. So,
# have django serve static files so apache isn't needed for development.
if settings.DEBUG:
  urlpatterns += patterns('',
      (r'^' + settings.MEDIA_URL[1:] + '(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': settings.MEDIA_ROOT}),
  )