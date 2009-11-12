from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('installer_creator.xmlrpc.dispatcher',
                       
                       (r'', 'rpc_handler', {}, 'rpc_handler'),
                       
                      )
