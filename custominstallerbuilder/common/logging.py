"""
<Program Name>
  logging.py

<Started>
  December 2010

<Author>
  Alex Hanson

<Purpose>
  Provides a log_exception() function that can be called in the except portion
  of a try...except block to log a formatted traceback to sys.stderr.
  
  For exceptions that were not explicitly caught in a try...except block,
  provides an AutoLogger class that serves as Django middleware, calling
  log_exception() automatically.
"""

import sys
import traceback


def _indent_string(string, num_spaces):
  lines = string.strip(' \n').split('\n')

  for line_num, line in enumerate(lines):
    lines[line_num] = (num_spaces * ' ') + line

  return '\n'.join(lines)


def log_exception(request=None):
  """
  <Purpose>
    Write details regarding the latest thrown exception to sys.stderr. On a web
    server, this should send the information to the server error log.
    
  <Arguments>
    request:
      An optional HttpRequest object, used for providing additional detail.
      
  <Exceptions>
    None. Throwing an exception here would be pretty ironic.
    
  <Side Effects>
    None.
    
  <Returns>
    None.
  """
  
  # By default, do not indent any messages.
  indentation = 0
  
  # Log the URL if a request object was given.
  if request is not None:
    url = request.build_absolute_uri()
    sys.stderr.write('Error while generating ' + url + '\n')
    
    # If a URL is printed, then indent the traceback.
    indentation = 2

  traceback_string = _indent_string(traceback.format_exc(), indentation)
  sys.stderr.write(traceback_string + '\n')
  sys.stderr.flush()





class AutoLogger(object):
  """
  <Purpose>
    If an exception is not explicitly caught somewhere, this class will
    write the details to the error log. It is meant to be used Django
    middleware.
    
    By default, uncaught exceptions will generate an HTTP 500 error (and a
    traceback page if in debug mode), but are seemingly not logged by the web
    server. This middleware fixes that by manually printing tracebacks to
    sys.stderr.
  
  <Side Effects>
    None.
  
  <Example Use>
    In the Django settings file (settings_base.py), add the following entry to
    the MIDDLEWARE_CLASSES list:
    
      'custominstallerbuilder.common.logging.AutoLogger'
  """
  
  def process_exception(self, request, exception):
    log_exception(request)
