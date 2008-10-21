from django.conf.urls.defaults import *
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('geni.control.views',
                       (r'^user_info$', 'user_info', {}, 'user_info'),
                       (r'^donations$', 'donations', {}, 'donations'),
                       (r'^used_resources$', 'used_resources', {}, 'used_resources'),
                       

                       # used_info functions:
                       (r'^gen_new_key$', 'gen_new_key', {}, 'gen_new_key'),
                       (r'^del_priv$', 'del_priv', {}, 'del_priv'),
                       (r'^priv_key$', 'dl_priv_key', {}, 'priv_key'),
                       (r'^pub_key$', 'dl_pub_key', {}, 'pub_key'),

                       # donations functions
                       (r'^new_share$', 'new_share', {}, 'new_share'),
                       (r'^del_share$', 'del_share', {}, 'del_share'),
)
