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
import getopt
import os
import sshxmlrpc


xmlrpc_server = "boss.emulab.net"
PACKAGE_VERSION = 0.1


# NEEDS TO BE CHANGED TO AUTOGRADER USER
login_id = "jenn"

# where do we connect to for xmlrpc commands
URI = "ssh://" + login_id + "@" + xmlrpc_server + "/xmlrpc";

# Get a handle on the server,
emulab_server = sshxmlrpc.SSHServerProxy(URI, path=None,
                        user_agent="sshxmlrpc_client-v0.1")


def startexp(proj,exp,nsfilestr,batch=False):
  """
  <Purpose>
    Starts a new expirament in emulab.  This is called once per expirament
    and then never called again.

  <Arguments>
    proj: a String that is the name of the emulab project.  Should be "Seattle"
    exp:  a String that is the unique name of the expirament
    nsfilestr:  a String representation of the expiraments ns file
    batch: wether or not this is a batch mode expirement, defaults to false   
 
  
  <Exceptions>
    If the emulab server reports that the operation was not a success
    for any reason an exception is thrown

  <Side Effects>
    None

  <Returns>
    Nothing

  """
  response=do_method("experiment.startexp",
  {"proj":proj,"exp":exp,"nsfilestr":nsfilestr,"batch":batch})
  
  check_response(response)


def endexp(proj,exp):
  """
  <Purpose>
    Ends an expirament.  This removes the expirament from emulab completly and
    should not be called until all autograding for the project is complete

  <Arguments>
    proj: a String that is the name of the emulab project.  Should be "Seattle"
    exp:  a String that is the unique name of the expirament
  
  <Exceptions>
    If the emulab server reports that the operation was not a success
    for any reason an exception is thrown

  <Side Effects>
    None

  <Returns>
    Nothing
 
  """
  response=do_method("experiment.endexp",{"proj":proj,"exp":exp})
  check_response(response)


def modexp(proj,exp,nsfilestr):
  """
  <Purpose>
    Modifies a previously existing expirament with a new or edited ns file.
    To run the expirament after modication call swapin. 

  <Arguments>
    proj: a String that is the name of the emulab project.  Should be "Seattle"
    exp:  a String that is the unique name of the expirament
    nsfilestr:  a String representation of the expiraments ns file

  <Exceptions>
    If the emulab server reports that the operation was not a success
    for any reason an exception is thrown

  <Side Effects>
    None

  <Returns>
    Nothing

  """
  response=do_method("experiment.modify",
    {"proj":proj,"exp":exp,"nsfilestr":nsfilestr})
  
  check_response(response)



def checkNS(nsfilestr):
  """
  <Purpose>
    Parse an ns file and look for any syntax errors. 

  <Arguments>
    nsfilestr:  a String representation of the expiraments ns file

  <Exceptions>
    If the emulab server reports that the operation was not a success
    for any reason an exception is thrown
  
  <Side Effects>
    None
  
  <Returns>
    A tupe of the form (Bool,String).  The Bool is True if the nsfile
    had no errors.  The string is the error message that was returned
    from emulab.  The string only needs to be checked if the Bool is 
    False.

  """
  response = do_method("experiment.nscheck",{"nsfilestr":nsfilestr})
  
  #if the emulab command failed throw an exception
  if (response['code'] != 0 and response['code'] !=2):
    check_response(response)
  
  #otherwise reutrn wether or not the ns file is correct
  else:
    return ((response['code']==0),response['output'])


def swapIN(proj,exp):
  """
  <Purpose>
    Starts a previously existing expirament.

  <Arguments>
    proj: a String that is the name of the emulab project.  Should be "Seattle"
    exp:  a String that is the unique name of the expirament

  <Exceptions>
    If the emulab server reports that the operation was not a success
    for any reason an exception is thrown

  <Side Effects>
    None

  <Returns>
    Nothing

  """
  response = do_method("experiment.swapexp",
    {"proj":proj,"exp":exp,"direction":"in"})
  check_response(response)



def swapOUT(proj,exp):
  """
  <Purpose>
    Stops an expirament that is currently running.

  <Arguments>
    proj: a String that is the name of the emulab project.  Should be "Seattle"
    exp:  a String that is the unique name of the expirament

  <Exceptions>
    If the emulab server reports that the operation was not a success
    for any reason an exception is thrown

  <Side Effects>
    None

  <Returns>
    Nothing

  """
  response = do_method("experiment.swapexp",{"proj":proj,
    "exp":exp,"direction":"out"})
  check_response(response)


def get_mapping(proj,exp):
  """
  <Purpose>
    Gets information about mappings from qualifed to physical nodes 
    in an active expirament

  <Arguments>
    proj: a String that is the name of the emulab project.  Should be "Seattle"
    exp:  a String that is the unique name of the expirament
  
  <Exceptions>
    If the emulab server reports that the operation was not a success
    for any reason an exception is thrown

  <Side Effects>
    None

  <Returns>
    a dictionary the key:value -> nodeName:dict of info about that node

  """
  response = do_method("experiment.info",
    {"proj":proj,"exp":exp,"aspect":"mapping"})
  check_response(response)
  return response['value']


def get_links(proj,exp):
  """
  <Purpose>
    Gets information about network links in an active expirement

  <Arguments>
    proj: a String that is the name of the emulab project.  Should be "Seattle"
    exp:  a String that is the unique name of the expirament

  <Exceptions>
    If the emulab server reports that the operation was not a success
    for any reason an exception is thrown

  <Side Effects>
    None

  <Returns>
    a dictionary containing information about network links

  """
  response = do_method("experiment.info",
    {"proj":proj,"exp":exp,"aspect":"links"})
  check_response(response)
  return response['value']



 
def simplify_links(proj,exp,links): 
  """
  <Purpose>
    simplifies links dictionary returned by get_links

  <Arguments>
    links - a dictionary of link information returned from get_links
    proj - the name of the emulab project
    exp - the name of the emulab expirament

  <Exceptions>
    If the emulab server reports that the operation was not a success
    for any reason an exception is thrown

  <Side Effects>
    None

  <Returns>
    a list of tuples with (nodename,nodeip)

  """
  simple_links =[]  

  for key in links:
    (node_name,x,y) = key.rpartition(':')
    node_name = node_name+"."+exp+"."+proj+".emulab.net"
    simple_links.append((node_name,links[key]['ipaddr']))

  return simple_links


def wait_for_active(proj,exp,timeout=600):
  """
  <Purpose>
    Blocks until the exp goes active or the timeout is reached

  <Arguments>
    proj: a String that is the name of the emulab project.  Should be "Seattle"
    exp:  a String that is the unique name of the expirament
    timeout: how many seconds to wait, 600 by default

  <Exceptions>
    If the emulab server reports that the operation was not a success
    for any reason an exception is thrown

  <Side Effects>
    None

  <Returns>
    nothing

  """
  response = do_method("experiment.waitforactive",
    {"proj":proj,"exp":exp,"timeout":timeout})
  check_response(response)


def wait_for_swapped(proj,exp,timeout=600):
  """
  <Purpose>
    Blocks until the exp goes to swapped or the timeout is reached

  <Arguments>
    proj: a String that is the name of the emulab project.  Should be "Seattle"
    exp:  a String that is the unique name of the expirament
    timeout: how many seconds to wait, 600 by default

  <Exceptions>
    If the emulab server reports that the operation was not a success
    for any reason an exception is thrown

  <Side Effects>
    None

  <Returns>
    nothing

  """
  response = do_method("experiment.statewait",
    {"proj":proj,"exp":exp,"state":"swapped","timeout":timeout})
  check_response(response)






#methods below are only intended to be called internally

# throw an exception if emulab does not succeed
def check_response(response):
 if response['code'] != 0:  #NOT A SUCCESS
    raise Exception(("Code "+str(response['code'])+" "+str(response['output'])))


# execute a single command
def do_method(methodname,params,server=emulab_server):

    # format the method call from xmlrpc 
    meth = getattr(server, methodname)

    # format the arguments for xmlrpc
    meth_args = [ PACKAGE_VERSION, params ]

    # Make the call. 
    try:
        response = apply(meth, meth_args)
        pass
    
    # did an error occur while connecting
    except sshxmlrpc.BadResponse, e:
        print ("error: bad reponse from host, " + e.args[0]
               + ", and handler: " + e.args[1])
        print "error: " + e.args[2]
        return -1
    
    # did an error occur internally to the emulab
    # xmlrpc library
    except sshxmlrpc.xmlrpclib.Fault, e:
        print e.faultString
        return -1

    
    return response

