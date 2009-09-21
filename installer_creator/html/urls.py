from django.conf.urls.defaults import *
from installer_creator.html import views

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('installer_creator.html.views',
                       
                       (r'^installer_creator$', 'installer_creator', {}, 'installer_creator'),
                       (r'^check_session$', 'check_session', {}, 'check_session'),
                       (r'^add_user$', 'add_user', {}, 'add_user'),
                       (r'^create_installer$', 'create_installer', {}, 'create_installer'),
                       (r'^download_keys$', 'download_keys', {}, 'download_keys'),
                       (r'^dl_keys$', 'dl_keys', {}, 'dl_keys'),
                       (r'^post_install$', 'post_install', {}, 'post_install'),
                       (r'^installers/(?P<installer_id>\w{' + str(views.INSTALLER_ID_LENGTH) + '})$', 'download_installers', {}, 'download_installers'),
                      )
