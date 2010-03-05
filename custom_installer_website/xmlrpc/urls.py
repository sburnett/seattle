from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('custom_installer_website.xmlrpc.dispatcher',
                       
                       (r'', 'rpc_handler', {}, 'rpc_handler'),
                       
                      )
