"""
<Program>
  exceptions.py

<Started>
  23 October 2009

<Author>
  Jason Chen
  jchen@cs.washington.edu
  
<Purpose>
  Defines custom exceptions for the Installer Creator.
"""

class InstallerCreatorError(Exception):
  """
  <Purpose>
    All other custom exceptions of seattlegeni inherit from this.
  """

class InvalidRequestError(InstallerCreatorError):
  """
  Indicates that a requested action was invalid. This is an intentionally
  generic error. This error should be raised with a message that clearly
  explains what was invalid.
  """