from django.conf.urls.defaults import *
from custom_installer_website.html import views

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('custom_installer_website.html.views',
                       
                       (r'^custom_installer_website$', 'custom_installer_website', {}, 'custom_installer_website'),
                       (r'^check_session$', 'check_session', {}, 'check_session'),
                       (r'^add_user$', 'add_user', {}, 'add_user'),
                       (r'^create_installer$', 'create_installer', {}, 'create_installer'),
                       (r'^download_keys$', 'download_keys', {}, 'download_keys'),
                       (r'^dl_keys$', 'dl_keys', {}, 'dl_keys'),
                       #(r'^post_install$', 'post_install', {}, 'post_install'),
                       (r'^installers/(?P<installer_id>.*)$', 'download_installers', {}, 'download_installers'),
                      )
