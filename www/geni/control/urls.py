from django.conf.urls.defaults import *
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('geni.control.views',
                       (r'^donations$', 'donations', {}, 'donations'),
                       (r'^used_resources$', 'used_resources', {}, 'used_resources'),
                       (r'^user_info$', 'user_info', {}, 'user_info'),
                       (r'^gen_new_key$', 'gen_new_key', {}, 'gen_new_key'),
                       (r'^del_priv$', 'del_priv', {}, 'del_priv'),
                       (r'^priv_key$', 'dl_priv_key', {}, 'priv_key'),
                       (r'^pub_key$', 'dl_pub_key', {}, 'pub_key')
)
