from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('web_installers.customized_installer.views',
                       # Example:
                       (r'^$', 'customized_installer' ,{}, 'customized_installer'),
                       (r'^help$', 'help' ,{}, 'help'),
                       (r'^build_installer$', 'build_installer' ,{}, 'build_installer'),
                       (r'^reset_form$', 'reset_form' ,{}, 'reset_form'),
                       (r'^downloads$', 'downloads' ,{}, 'downloads')
                       
                       
                       # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
                       # to INSTALLED_APPS to enable admin documentation:
                       # (r'^admin/doc/', include('django.contrib.admindocs.urls')),
                       
                       # Uncomment the next line to enable the admin:
                       # (r'^admin/(.*)', admin.site.root),
)
