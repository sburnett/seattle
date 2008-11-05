from django.conf.urls.defaults import *
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('geni.control.views',
                       (r'^user_info$', 'user_info', {}, 'user_info'),
                       (r'^donations$', 'donations', {}, 'donations'),
                       (r'^used_resources$', 'used_resources', {}, 'used_resources'),
                       
                       # used_resources functions:
                       (r'^get_resources$', 'get_resources', {}, 'get_resources'),
                       (r'^del_resource$', 'del_resource', {}, 'del_resource'),
                       (r'^del_all_resource$', 'del_all_resources', {}, 'del_all_resources'),
                       
                       # user_info functions:
                       (r'^gen_new_key$', 'gen_new_key', {}, 'gen_new_key'),
                       (r'^del_priv$', 'del_priv', {}, 'del_priv'),
                       (r'^priv_key$', 'dl_priv_key', {}, 'priv_key'),
                       (r'^pub_key$', 'dl_pub_key', {}, 'pub_key'),

                       # donations functions
                       (r'^new_share$', 'new_share', {}, 'new_share'),
                       (r'^del_share$', 'del_share', {}, 'del_share'),
)
