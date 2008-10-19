from django.conf.urls.defaults import *
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('geni.control.views',
                       (r'^$', 'main'),
                       (r'^add_share/$', 'add_share')
)
