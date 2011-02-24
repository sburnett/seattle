"""
<Program Name>
  urls.py

<Started>
  September 2010

<Author>
  Alex Hanson

<Purpose>
  A standard Django URL configuration that delegates between URLs intended for
  the HTML and XML-RPC interfaces to the Custom Installer Builder. Also
  initiates a static file server if local settings call for it.
"""

from django.conf.urls.defaults import include, patterns, url
from django.conf import settings


# Display errors gracefully.
handler500 = 'custominstallerbuilder.html.views.error_page'

urlpatterns = patterns('',
  # XML-RPC URL patterns. Matches all URLs which start with 'xmlrpc' followed
  # by a slash.
  #   Example: http://example.com/custominstallerbuilder/xmlrpc/[...]
  url(r'^xmlrpc/', include('custominstallerbuilder.xmlrpc.urls')),

  # HTML URL patterns. Matches all URLs not caught by other patterns (XML-RPC
  # above or the optional static server below).
  #   Example: http://example.com/custominstallerbuilder/
  #        or  http://example.com/custominstallerbuilder/ajax/build/
  url(r'', include('custominstallerbuilder.html.urls')),
)

# Use the 'SERVE_STATIC' and 'STATIC_BASE' custom settings to determine if
# Django should serve static files itself. This is useful for debugging.
if getattr(settings, 'SERVE_STATIC', False):
  
  # Matches URLs which start with the contents of STATIC_BASE as specified in
  # settings.py, followed by a slash then any string. That string is
  # interpreted as a path for a file to lookup.
  #   Example: http://example.com/custominstallerbuilder/static/[...]
  regex = r'^%s/(?P<path>.*)$' % settings.STATIC_BASE.rstrip('/')
  
  urlpatterns += patterns('',
    url(regex, 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT, 'show_indexes': settings.DEBUG}),
  )