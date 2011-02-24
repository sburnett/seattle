"""
<Program Name>
  urls.py

<Started>
  September 2010

<Author>
  Alex Hanson

<Purpose>
  A standard Django URL configuration for the HTML functionality of the
  Custom Installer Builder.
"""

from django.conf.urls.defaults import patterns, url

import custominstallerbuilder.common.constants as constants


urlpatterns = patterns('custominstallerbuilder.html.views',

  # Builder interface.
  
  # These patterns match the string between ^ and $ against the end portion of
  # the URL.
  #   Example: http://example.com/custominstallerbuilder/
  #        or  http://example.com/custominstallerbuilder/ajax/build/
  url(r'^$', 'builder_page', name='builder'),
  url(r'^ajax/build/$', 'build_installers', name='ajax-build'),
  url(r'^ajax/save/$', 'save_state', name='ajax-save'),
  url(r'^ajax/restore/$', 'restore_state', name='ajax-restore'),
  url(r'^ajax/reset/$', 'reset_state', name='ajax-reset'),
  url(r'^ajax/add-user/$', 'add_user', name='ajax-add-user'),


  # Download pages.
  
  # This pattern matches against the end portion of a URL with a valid build
  # ID (as specified by custominstallerbuilder.common.constants.BUILD_ID_REGEX)
  # followed by a slash.
  #   Example: http://example.com/custominstallerbuilder/28d0ccc35d16fc9114f47f251968b3354183544c/
  url(r'^(?P<build_id>' + constants.BUILD_ID_REGEX + ')/$', 'download_installers_page', name='download-installers-page'),

  # This pattern extends the one above by appending 'keys/' to the URL.
  url(r'^(?P<build_id>' + constants.BUILD_ID_REGEX + ')/keys/$', 'download_keys_page', name='download-keys-page'),
  
  # This pattern extends the one above by further matching against a build ID
  # and two lowercase alphabetic strings, each followed by a slash.
  #   Example: http://example.com/custominstallerbuilder/28d0ccc35d16fc9114f47f251968b3354183544c/foo/bar/
  url(r'^(?P<build_id>' + constants.BUILD_ID_REGEX + ')/installers/(?P<platform>[a-z]+)/$',
       'download_installer', name='download-installer'),
  url(r'^(?P<build_id>' + constants.BUILD_ID_REGEX + ')/keys/(?P<key_type>[a-z]+)/$',
       'download_keys', name='download-keys'),
)
