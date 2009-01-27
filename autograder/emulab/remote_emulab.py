"""
<Program Name>
  remote_emulab.py

<Started>
  Jan 25 2009

<Author>
  kimbrl@cs.washington.edu
  Eric Kimbrel

<Purpose>
  This program provides methods that interface with emulabs XML_RPC server.  
  
  The intention of this program is for these methods to be called as part of
  the Seattle autograding framework

  SSH is used to connect to the emu lab server without having to provide a
  password.  SSH keys must manually be set up between the client running this 
  code and the emulab server.  The constant "login_id" below must be changed to
  the login matching the keys that will be used to connect.

  For this program to run in must import two EMU-LAB Programs, sshxmlrpc.py
  and emulabclient.py.

"""





import sys
sys.path.append("/usr/testbed/lib")
import getopt
import os

from sshxmlrpc import *
from emulabclient import *


xmlrpc_server = "boss.emulab.net"
PACKAGE_VERSION = 0.1

login_id = "kimbrl"

URI = "ssh://" + login_id + "@" + xmlrpc_server + "/xmlrpc";

# Get a handle on the server,
emulab_server = SSHServerProxy(URI, path=None,
                        user_agent="sshxmlrpc_client-v0.1")


def startexp(proj,exp,nsfilestr):
  """
  <Purpose>
    Starts a new expirament in emulab.  This is called once per expirament
    and then never called again.

  <Arguments>
    proj: a String that is the name of the emulab project.  Should be "Seattle"
    exp:  a String that is the unique name of the expirament
    nsfilestr:  a String representation of the expiraments ns file

  <Returns>
    Returns 0 if no errors occured.  Otherwise returns a string representing the error. 
    Emulab will send an email to the account used giving details of the expirament.

  """
  value=do_method("experiment.startexp",{"proj":proj,"exp":exp,"nsfilestr":nsfilestr})
  return value



def endexp(proj,exp):
 """
 <Purpose>
   Ends an expirament.  This removes the expirament from emulab completly and
   should not be called until all autograding for the project is complete

 <Arguments>
   proj: a String that is the name of the emulab project.  Should be "Seattle"
   exp:  a String that is the unique name of the expirament
 
 <Returns>
   Returns 0 if no errors occured.  Otherwise returns a string represent the error.
   Emulab will send an email to the account used giving details of the expirament

 """
 value=do_method("experiment.endexp",{"proj":proj,"exp":exp})
 return value


def modexp(proj,exp,nsfilestr):
  """
  <Purpose>
    Modifies a previously existing expirament with a new or edited ns file.
    To run the expirament after modication call swapin. 

  <Arguments>
    proj: a String that is the name of the emulab project.  Should be "Seattle"
    exp:  a String that is the unique name of the expirament
    nsfilestr:  a String representation of the expiraments ns file

  <Returns>
    Returns 0 if no errors occured. Otherwise returns a string representing the error.
    Emulab will send an email to the account used giving details of the expirament.

  """
  value=do_method("experiment.modify",{"proj":proj,"exp":exp,"nsfilestr":nsfilestr})
  return value



def checkNS(nsfilestr):
  """
  <Purpose>
    Parse an ns file and look for any syntax errors. 

  <Arguments>
    nsfilestr:  a String representation of the expiraments ns file

  <Returns>
    Returns 0 if no errors occured.  Otherwise returns a string representing
    the error
  """
  value = do_method("experiment.nscheck",{"nsfilestr":nsfilestr})
  return value


def swapIN(proj,exp):
  """
  <Purpose>
    Starts a previously existing expirament.

  <Arguments>
    proj: a String that is the name of the emulab project.  Should be "Seattle"
    exp:  a String that is the unique name of the expirament

  <Returns>
    Returns 0 if no errors occured.  Emulab will send an email to the account used
    giving details of the expirament

  """
  value = do_method("experiment.swapexp",{"proj":proj,"exp":exp,"direction":"in"})
  return value



def swapOUT():
  """
  <Purpose>
    Stops an expirament that is currently running.

  <Arguments>
    proj: a String that is the name of the emulab project.  Should be "Seattle"
    exp:  a String that is the unique name of the expirament

  <Returns>
    Returns 0 if no errors occured.  Emulab will send an email to the account used
    giving details of the expirament

  """
  value = do_method("experiment.swapexp",{"proj":proj,
    "exp":exp,"direction":"out"})
  return value




# The folling method is called privately from to connect to the emulab
# server and excute commands.  It was copied from sshxmlrpc_client.py 
# (copytrighted emulab software) and then modified be the author of the 
# rest of this program (Eric Kimbrel).  The EMU-Lab copy right allows 
# use, modification, and distribution of this software.  The copyright
# is provided here

# EMULAB-COPYRIGHT
# Copyright (c) 2004 University of Utah and the Flux Group.
# All rights reserved.
# 
# Permission to use, copy, modify and distribute this software is hereby
# granted provided that (1) source code retains these copyright, permission,
# and disclaimer notices, and (2) redistributions including binaries
# reproduce the notices in supporting documentation.
#
# THE UNIVERSITY OF UTAH ALLOWS FREE USE OF THIS SOFTWARE IN ITS "AS IS"
# CONDITION.  THE UNIVERSITY OF UTAH DISCLAIMS ANY LIABILITY OF ANY KIND
# FOR ANY DAMAGES WHATSOEVER RESULTING FROM THE USE OF THIS SOFTWARE.
#

# execute a single command
def do_method(methodname,params,server=emulab_server):

    meth = getattr(server, methodname)

    meth_args = [ PACKAGE_VERSION, params ]

    #
    # Make the call. 
    #
    try:
        response = apply(meth, meth_args)
        pass
    except BadResponse, e:
        print ("error: bad reponse from host, " + e.args[0]
               + ", and handler: " + e.args[1])
        print "error: " + e.args[2]
        return -1
    except xmlrpclib.Fault, e:
        print e.faultString
        return -1

    #
    # Parse the Response, which is a Dictionary. See EmulabResponse in the
    # emulabclient.py module. The XML standard converts classes to a plain
    # Dictionary, hence the code below. 
    # 
    if len(response["output"]):
        print response["output"]
        pass

    rval = response["code"]

    #
    # If the code indicates failure, look for a "value". Use that as the
    # return value instead of the code. 
    # 
    if rval != RESPONSE_SUCCESS:
        if response["value"]:
            rval = response["value"]
            pass
        pass

    #if debug and response["value"]:
     #   print str(response["value"])
      #  pass
        
    return rval
