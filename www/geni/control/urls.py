from django.conf.urls.defaults import *
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('geni.control.views',
                       (r'^donations$', 'donations'),
                       (r'^used_resources$', 'used_resources'),
                       (r'^user_info$', 'user_info', {}, 'user_info'),
                       
                       (r'^add_share$', 'add_share')
)
