from django.conf.urls.defaults import *
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('geni.download.views',
                       (r'^(?P<username>\w{3,32})/$', 'download', {}, 'installers'),
                       (r'^(?P<username>\w{3,32})/mac$', 'mac', {}, 'mac'),
                       (r'^(?P<username>\w{3,32})/linux$', 'linux', {}, 'linux'),
                       (r'^(?P<username>\w{3,32})/win$', 'win', {}, 'win'),
)
