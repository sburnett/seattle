"""
<Program>
  validations.py

<Started>
  13 September 2009

<Author>
  Jason Chen
  Justin Samuel

<Purpose>
  Validates input from HTML and XMLRPC installer creator views.
"""

import re

from seattle import repyhelper
from seattle import repyportability

repyhelper.translate_and_import("rsa.repy")

USERNAME_MIN_LENGTH = 3
USERNAME_MAX_LENGTH = 40
# In general, numbers, letters, and underscores are allowed in usernames.
USERNAME_ALLOWED_CHARS = r"0-9a-zA-Z_"
USERNAME_ALLOWED_REGEX = re.compile(r"^[" + USERNAME_ALLOWED_CHARS + "]+$")
# The first character of the username, however, we don't allow to be an underscore.
# We make this a separate regex so that it's easier to explain to the user
# if their username is denied.
USERNAME_ALLOWED_FIRST_CHARS = r"0-9a-zA-Z"
USERNAME_ALLOWED_FIRST_REGEX = re.compile(r"^[" + USERNAME_ALLOWED_FIRST_CHARS + "]")



def validate_username(username):
  """
  <Purpose>
    Determine whether username is a valid username.
  """
  try:
    assert_str(username)
  except AssertionError:
    raise ValidationError("Username must be a string.")
  
  if len(username) < USERNAME_MIN_LENGTH:
    raise ValidationError("Username must be at least " + str(USERNAME_MIN_LENGTH) + " characters.")
  
  if len(username) > USERNAME_MAX_LENGTH:
    raise ValidationError("Username must be less than " + str(USERNAME_MAX_LENGTH) + " characters.")
  
  if not USERNAME_ALLOWED_REGEX.match(username):
    raise ValidationError("Username can only contain the characters " + USERNAME_ALLOWED_CHARS)

  if not USERNAME_ALLOWED_FIRST_REGEX.match(username):
    raise ValidationError("Username must start with one of the characters " + USERNAME_ALLOWED_FIRST_CHARS)



def validate_pubkey_string(pubkeystring):
  """
  <Purpose>
    Determine whether a pubkey string looks like a valid public key.
  <Arguments>
    pubkeystring
      The string we want to find out if it is a valid pubkey string.
  <Exceptions>
    None
  <Side Effects>
    None
  <Returns>
    True if pubkeystring looks like a valid pubkey, False otherwise.
    Currently this uses functions that aren't conclusive about validity of the
    key, but for our purposes we just want to make sure it's generally the
    correct data format.
  """
  try:
    assert_str(pubkeystring)
  except AssertionError:
    raise ValidationError("Public key must be a string.")
  
  try:
    possiblepubkey = rsa_string_to_publickey(pubkeystring)
  except ValueError:
    raise ValidationError("Public key is not of a correct format.")

  if not rsa_is_valid_publickey(possiblepubkey):
    raise ValidationError("Public key is invalid.")



def assert_str(value):
  """
  <Purpose>
    Ensure that value is a string (can be str or unicode).
  """
  # Check for basestring which is the superclass of str and unicode.
  if not isinstance(value, basestring):
    raise AssertionError("Expected string value, received " + str(type(value)))



class ValidationError(Exception):
  """
  Indicates that some data checked for validity is invalid. This is not the
  same as a django.forms.ValidationError.
  """