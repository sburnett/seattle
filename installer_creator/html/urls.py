from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('installer_creator.html.views',
                       
                       (r'^installer_creator$', 'installer_creator',{},'installer_creator'),
                       (r'^add_user$', 'add_user', {}, 'add_user'),
                       (r'^create_installer$', 'create_installer', {}, 'create_installer'),
                       (r'^download_installers$', 'download_installers', {}, 'download_installers'),
                       
                      )
