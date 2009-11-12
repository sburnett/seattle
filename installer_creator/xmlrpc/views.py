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

import os
import traceback
import xmlrpclib        # Used for raising xmlrpc faults

from seattle import repyhelper
from seattle import repyportability

repyhelper.translate_and_import('rsa.repy')


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
    
    except Exception, e:
      # We assume all other exceptions are bugs in our code.

      # We use the log message as the basis for the email message, as well.
      logmessage = "Internal error while handling an xmlrpc request: " + traceback.format_exc()
      #log.critical(logmessage)

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
  def create_installer(geni_username, user_pubkey):
    """
    Called via XMLRPC by SeattleGENI to create installers.
    """
    # We know exactly the vesselinfo format needed for SeattleGENI installer,
    # so just construct it here directly, and pass it to the builder
    vesselinfo = "Percent 80\n"
    vesselinfo += "Owner " + user_pubkey + "\n"
    vesselinfo += "User " + builder.ACCEPTDONATIONS_STATE_PUBKEY + "\n"
    vesselinfo += "Percent 20\n"
    vesselinfo += "Owner " + builder.SEATTLE_OWNER_PUBKEY + "\n"
    
    # first check if this user has ever built an installer by trying to read the vesselinfo    
    dist_folder = os.path.join(settings.USER_INSTALLERS_DIR, geni_username + "_dist")
    
    #v_handle = open(os.path.join(os.path.join(dist_folder, "install_info"), "vesselinfo"), 'rb')
    v_handle = None
    
    installer_urls_dict = {}
    installer_urls_dict['w'] = settings.USER_INSTALLERS_URL + "%s_dist/seattle_win.zip"%(geni_username)
    installer_urls_dict['l'] = settings.USER_INSTALLERS_URL + "%s_dist/seattle_linux.tgz"%(geni_username)
    installer_urls_dict['m'] = settings.USER_INSTALLERS_URL + "%s_dist/seattle_mac.tgz"%(geni_username)
    
    print "searching for vesselinfo at: " + os.path.join(dist_folder, "install_info", "vesselinfo")
    try:
      v_handle = open(os.path.join(dist_folder, "install_info", "vesselinfo"), 'rb');
    except IOError:
      # No dist folder for this user, so we're going to setup & create a new installer.
      print "Couldn't find dist folder/vesselinfo for this user: creating new installer."
      builder.build_installer(vessel_dict = '', key_dict = '', 
                              username = geni_username, dist_str = 'wlm', 
                              vesselinfo = vesselinfo)
    else:
      # Found the vesselinfo, check if installer is out-of-date 
      print "Found dist folder, checking if installer is out-of-date"
      #vesselinfo_data = v_handle.read()
      v_handle.close()
      check_ret = builder.check_and_build_if_new_installers(geni_username)
      print "check_and_build returned: " + str(check_ret)
      if (check_ret == 0):      
        # either no rebuild was needed, or installers were out-of-date and rebuilt. either way, serve up urls
        print "[xmlrpc CREATE_INSTALLER]: serving up cached installers." 
        return installer_urls_dict
      elif (check_ret == 1):
        print "[xmlrpc CREATE_INSTALLER]: serving up rebuilt, up-to-date installers." 
        return installer_urls_dict
      else:
        # something went wrong during the check, eg: base installers not found
        # TODO: What do we return if something goes wrong?
        print "[xmlrpc CREATE_INSTALLER]: check_and_build returned fatal -1"
        return 0
    
    print "[xmlrpc CREATE_INSTALLER]: serving up fresh installers."
    return installer_urls_dict