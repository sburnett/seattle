"""
<Program Name>
  validations.py

<Started>
  September 2010

<Author>
  Alex Hanson

<Purpose>
  Provides a set of tests to help validate user input to the Custom
  Installer Builder. Also provides a set of constants and exceptions useful
  toward that end.
"""

import os
import re

from django.conf import settings

import custominstallerbuilder.common.constants as constants



################
## Exceptions ##
################

class ValidationError(Exception):
  """This exception indicates the user provided us with invalid input."""
  pass





###########
## Tests ##
###########

def validate_build_id(build_id):
  """
  <Purpose>
    Performs basic validation upon the provided build ID.
  <Arguments>
    build_id:
      The build ID to be checked against.
  <Exceptions>
    ValidationError if the build_id is invalid.
  <Side Effects>
    None.
  <Returns>
    None.
  """
  
  # Matches a string which follows the rules for build IDs, as given by
  # custominstallerbuilder.common.constants.BUILD_ID_REGEX
  if not re.match(r'^' + constants.BUILD_ID_REGEX + '$', build_id):
    raise ValidationError('Invalid build_id provided.')




def validate_public_key(public_key):
  """
  <Purpose>
    Performs basic validation upon the provided public key.
  <Arguments>
    public_key:
      The public key to be validated.
  <Exceptions>
    ValidationError if public_key is invalid.
  <Side Effects>
    None.
  <Returns>
    None.
  """
  
  # Matches strings which start with a series of one or more digits, then a
  # single space, then end with another series of one or more digits. All
  # public keys should match this form.
  if not re.match(r'^\d+ \d+$', public_key):
      raise ValidationError('Invalid public key provided.')





def validate_percentage(percentage):
  """
  <Purpose>
    Ensures that the given percentage value is an integer between 1 and 100,
    inclusive.
  <Arguments>
    percentage:
      The percentage value to be validated.
  <Exceptions>
    ValidationError if percentage is invalid.
  <Side Effects>
    None.
  <Returns>
    None.
  """
  
  if not isinstance(percentage, int) and not isinstance(percentage, long):
    raise ValidationError('Percentage should be of type int or long.')
      
  if percentage < 1:
    raise ValidationError('Percentage should be a positive integer.')
    
  if percentage > 100:
    raise ValidationError('Percentage should not exceed 100.')





def validate_percentage_total(current_percentage):
  """
  <Purpose>
    Ensures that the given percentage value matches the required percentage for
    a proper build. For example, if 20% of resources are reserved, then the
    percentage total across all vessels should equal 80%.
  <Arguments>
    current_percentage:
      The percentage value to be validated.
  <Exceptions>
    ValidationError if current_percentage does not match the required_percentage.
  <Side Effects>
    None.
  <Returns>
    None.
  """
  
  required_percentage = 100 - settings.RESERVED_PERCENTAGE

  if current_percentage != required_percentage:
    raise ValidationError(('Vessel resources must total ' + str(required_percentage) +
      '% exactly. Current vessels total ' + str(current_percentage) + '%.'))





def validate_platform(platform):
  """
  <Purpose>
    Ensures that the given value is a platform which the installer builder
    can actually build.
  <Arguments>
    platform:
      The platform string to be validated.
  <Exceptions>
    ValidationError if platform is invalid.
  <Side Effects>
    None.
  <Returns>
    None.
  """
  
  if platform not in constants.PLATFORMS:
    raise ValidationError('Invalid platform specified.')





def validate_username(username):  
  """
  <Purpose>
    Performs validation upon the given user name for length and content.
  <Arguments>
    username:
      The user name to be validated.
  <Exceptions>
    ValidationError if username is invalid.
  <Side Effects>
    None.
  <Returns>
    None.
  """
    
  if len(username) < constants.USERNAME_RULES['min_length']:
    raise ValidationError('Username must be at least ' + str(constants.USERNAME_RULES['min_length']) + ' characters long.')

  if len(username) > constants.USERNAME_RULES['max_length']:
    raise ValidationError('Username must not exceed ' + str(constants.USERNAME_RULES['max_length']) + ' characters in length.')
  
  # Matches strings composed entirely of characters specified within
  # custominstallerbuilder.common.constants.USERNAME_RULES['valid_chars']
  if not re.match(r'^[' + constants.USERNAME_RULES['valid_chars'] + ']+$', username):
    raise ValidationError('Username can only contain these characters: ' + constants.USERNAME_RULES['valid_chars'])

  # Matches strings whose first character is specified within
  # custominstallerbuilder.common.constants.USERNAME_RULES['valid_first_chars']
  if not re.match(r'^[' + constants.USERNAME_RULES['valid_first_chars'] + ']', username):
    raise ValidationError('Username must start with one of these characters: ' + constants.USERNAME_RULES['valid_first_chars'])
