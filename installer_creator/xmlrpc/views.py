"""
<Program>
  views.py

<Started>
  23 October 2009

<Author>
  Jason Chen
  jchen@cs.washington.edu

<Purpose>
  This file defines all of the public Installer Creator functions. When the 
  Installer Creator XMLRPC API changes, this file will generally always
  need to be modified.  

  To create a new xmlrpc function, just create a new method in the
  PublicXMLRPCFunctions class below. All public methods in that class
  are automatically registered with the xmlrpc dispatcher.

  The functions defined here should generally be making calls to the
  controller interface to perform any work or retrieve data.

  Be sure to use the following decorators with each function, in this order:

  @staticmethod -- this is a python decorator that prevents 'self'
                   from being passed as the first argument.
  @log_function_call -- this is our own decorator for logging purposes.
"""

import django.core.mail # To send the admins emails when there's an unhandled exception.
from installer_creator.common.validations import ValidationError

import os
import traceback
import xmlrpclib        # Used for raising xmlrpc faults

#from seattle import repyhelper
#from seattle import repyportability

#repyhelper.translate_and_import('rsa.repy')

from installer_creator import settings
from installer_creator.common import builder
from installer_creator.common import validations
from installer_creator.common.exceptions import *

# XMLRPC Fault Code Constants
FAULTCODE_OPERROR = 100
FAULTCODE_AUTHERROR = 101
FAULTCODE_INVALIDUSERINPUT = 102
FAULTCODE_NOTENOUGHCREDITS = 103
FAULTCODE_KEYALREADYREMOVED = 104

class PublicXMLRPCFunctions(object):
  """
  All public functions of this class are automatically exposed as part of the
  xmlrpc interface.
  
  Each method should be sure to check the user input and return useful errors
  to the client if the input is invalid. Note that raising an AssertionError
  (e.g. through a call to an assert_* method) won't be sufficient, as those
  should only indicate something going wrong in our code. 
  """

  def _dispatch(self, method, args):
    """
    We provide a _dispatch function (which SimpleXMLRPCServer looks for and
    uses) so that we can log exceptions due to our programming errors within
    seattlegeni as well to detect incorrect usage by clients.
    """
    
    try:
      # Get the requested function (making sure it exists).
      try:
        func = getattr(self, method)
      except AttributeError:
        raise InvalidRequestError("The requested method '" + method + "' doesn't exist.")
      
      # Call the requested function.
      return func(*args)
    
    except InvalidRequestError:
      #log.error("The xmlrpc server was used incorrectly: " + traceback.format_exc())
      raise
    
    except xmlrpclib.Fault:
      # A xmlrpc Fault was intentionally raised by the code in this module.
      raise
    
    except validations.ValidationError:
      # Validation error!
      print "Caught a validation error!"
      raise
    
    except Exception, e:
      # We assume all other exceptions are bugs in our code.

      # We use the log message as the basis for the email message, as well.
      logmessage = "Internal error while handling an xmlrpc request: " + traceback.format_exc()
      #log.critical(logmessage)
      print logmessage
      
      # Normally django will send an email to the ADMINS defined in settings.py
      # when an exception occurs. However, our xmlrpc dispatcher will turn this
      # into a Fault that is returned to the client. So, django won't see it as
      # an uncaught exception. Therefore, we have to send it ourselves.
      if not settings.DEBUG:
        subject = "Error handling xmlrpc request '" + method + "': " + str(type(e)) + " " + str(e)
        
        emailmessage = logmessage + "\n\n"
        emailmessage += "XMLRPC method called: " + method + "\n"
        
        # If the first argument looks like auth info, don't include the
        # api_key in the email we send. Otherwise, include all the args.
        # We wrap this in a try block just in case we screw this up we want to
        # be sure we get an email still.
        try:
          if len(args) > 0 and isinstance(args[0], dict) and "username" in args[0]:
            emailmessage += "Username: " + str(args[0]["username"]) + "\n"
            if len(args) > 1:
              emailmessage += "Non-auth arguments: " + str(args[1:]) + "\n"
            else:
              emailmessage += "There were no non-auth arguments." + "\n"
          else:
            emailmessage += "Arguments: " + str(args) + "\n"
        except:
          pass
          
        # Send an email to the addresses listed in settings.ADMINS
        # django.core.mail.mail_admins(subject, emailmessage)
      
      # It's not unlikely that the user ends up seeing this message, so we
      # are careful about what the content of the message is. We don't
      # include the exception trace.
      #raise xmlrpclib.Fault(FAULTCODE_OPERROR, "Internal error while handling the xmlrpc request.")
      raise
      

  @staticmethod
  def create_installer(vessel_list, pubkey_dict, os):
    """
    <Purpose>
      An XMLRPC method to create installers.
    
    <Arguments>
      vessel_list:
        A list of vessel dictionaries, each dict representing a defintion
        of a vessel. Follows the format:
        [ {owner, percentage, [users]}, {owner, percentage, [users]} ... ]
        
        NOTE: Percentages MUST add up to 80 (20 reserved for Seattle),
              or the creation will fail.
      
      pubkey_dict:
        A dictionary whose keys are usernames, and whose 
        values are pubkeys. Follows the format:
        { 'user1' : 'pubkey', 'user2' ... }
    
      os:
        A string indicating which OS to build the installer for.
        Valid strings are: 'windows', 'linux', 'mac'
    
    <Returns>
      A URL at which the created installer is accessible from.
    """
    
    # Validate the input
    validate_xmlrpc_input(vessel_list, pubkey_dict, os);
    
    # We've told users to make sure percentages add up to 100 since it 
    # makes more sense. But, the prepare method expects percentages to 
    # add up to 10. So, divide.
    for vessel in vessel_list:
      vessel['percentage'] /= 10;
    
    # Generate build ID
    build_id = builder.generate_build_id(vessel_list, pubkey_dict)
    print "[xmlrpc CREATE_INSTALLER]: build_id: " + build_id
    
    builder.prepare_installer(vessel_list, pubkey_dict, build_id)
    
#    dist_folder = os.path.join(settings.USER_INSTALLERS_DIR, build_id + "_dist")
#    installer_urls_dict = {}
#    installer_urls_dict['w'] = settings.USER_INSTALLERS_URL + "%s_dist/seattle_win.zip"%(build_id)
#    installer_urls_dict['l'] = settings.USER_INSTALLERS_URL + "%s_dist/seattle_linux.tgz"%(build_id)
#    installer_urls_dict['m'] = settings.USER_INSTALLERS_URL + "%s_dist/seattle_mac.tgz"%(build_id)
    
    if (os == 'windows'):
      installer_url = settings.USER_INSTALLERS_URL + build_id + "/seattle_win.zip"
    elif (os == 'linux'):
      installer_url = settings.USER_INSTALLERS_URL + build_id + "/seattle_linux.tgz"
    elif (os == 'mac'):
      installer_url = settings.USER_INSTALLERS_URL + build_id + "/seattle_mac.tgz"
    
    return installer_url



def validate_xmlrpc_input(vessel_list, pubkey_dict, os):
  # TODO: catch validation exceptions
    
    validations.assert_list(vessel_list)
    validations.assert_dict(pubkey_dict)
    validations.assert_str(os)
    
    total_percentage = 0;
    
    for vessel in vessel_list:
      validations.assert_str(vessel['owner'])
      validations.assert_positive_int(vessel['percentage'])
      total_percentage += vessel['percentage']
      try:
        validations.assert_list(vessel['users'])
      except KeyError:
        raise ValidationError("Missing users list in a vessel dict")
    
    # check that vessel percentages add up to 80
    if (total_percentage != 80):
      raise ValidationError("Vessel percentages must add up to 80! (20% is reserved for Seattle)")
    
    for user in pubkey_dict:
      validations.assert_str(pubkey_dict[user]['pubkey'])
    
    if ((os != 'windows') and (os != 'linux') and (os != 'mac')):
      raise ValidationError("Invalid OS selection.")