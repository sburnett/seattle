from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('installer_creator.html.views',
                       
                       (r'^installer_creator$', 'installer_creator',{},'installer_creator'),
                       (r'^reset_form$', 'reset_form', {}, 'reset_form'),
                       
                      )
