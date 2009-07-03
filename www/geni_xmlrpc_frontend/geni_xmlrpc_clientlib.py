"""
<Program Name>
  geni_xmlrpc_clientlib.py

<Started>
  6/28/2009

<Author>
  Jason Chen
  jchen@cs.washington.edu
  
<Purpose>
  A client 'library' for communicating with the SeattleGENI XMLRPC Server.
  Clients can import this library, create an instance of the 'client' object,
  then invoke 'client' methods. These calls are translated to actual SeattleGENI
  XMLRPC calls, and after the XMLRPC call is completed, the results are returned
  back to the user.
"""

import xmlrpclib
# check to see if M2Crypto is installed
#try:
#  import M2Crypto
#except ImportError, err:
#  print "!!! ERROR: M2Crypto is not installed."
#  print "!!! Please make sure M2Crypto is properly installed into your Python distribution."

class client:
  def __init__(self, username, authstring,
               xmlrpc_url='https://seattlegeni.cs.washington.edu:443/xmlrpc/', 
               allow_ssl_insecure=False):
    if not username or not authstring or not xmlrpc_url:
      raise ValueError("Parameters were invalid, please check your parameters.")
    elif allow_ssl_insecure == False:
      raise ValueError("WARNING: Operation of SSL in a secure manner is not available yet. Check the Seattle project website to ensure you have the latest version of geni_xmlrpc_clientlib.")

    # build authorization dict
    auth = {'username':username, 'authstring':authstring}
    self.auth = auth
    self.xmlrpc_url = xmlrpc_url
    self.allow_ssl_insecure = allow_ssl_insecure
  
  def warmup(self):
    #self.proxy = M2Crypto.m2xmlrpclib.Server(self.xmlrpc_url,
    #             M2Crypto.m2xmlrpclib.SSL_Transport())
    self.proxy = xmlrpclib.Server(self.xmlrpc_url)

    # check auth is valid
    if(self.proxy.authcheck(self.auth) != 0):
      raise GENI_AuthError
      
  def acquire_lan_resources(self, num):
    return self.acquire_resources('lan', num)

  def acquire_wan_resources(self, num):
    return self.acquire_resources('wan', num)

  def acquire_random_resources(self, num):
    return self.acquire_resources('random', num)
    
  def acquire_resources(self, res_type, num):
    rspec = {'rspec_type':res_type, 'number_of_nodes':num}
    try:
      acquired_dict = self.proxy.acquire_resources(self.auth, rspec)
    except xmlrpclib.Fault, fault:
      if str(fault).startswith("<Fault 100") and str(fault).endswith(">"):
        raise GENI_OpError
      elif str(fault).startswith("<Fault 102") and str(fault).endswith(">"):
        raise GENI_NotEnoughCredits
      elif str(fault).startswith("<Fault 103") and str(fault).endswith(">"):
        raise GENI_NoAvailNodes
      elif 'TypeError' in str(fault):
        raise TypeError(str(fault))
      elif 'ValueError' in str(fault):
        raise ValueError(str(fault))
      else:
        print(str(fault))
    else:
      return acquired_dict
      
  def release_resources(self, handlelist):
    if not handlelist:
      raise ValueError("Given handlelist is empty.")
    try:
      self.proxy.release_resources(self.auth, handlelist)
    except xmlrpclib.Fault, fault:
      if str(fault).startswith("<Fault 100") and str(fault).endswith(">"):
        raise GENI_OpError
      elif 'TypeError' in str(fault):
        raise TypeError(str(fault))

  def get_resource_info(self):
    return self.proxy.get_resource_info(self.auth)
      
  def get_account_info(self):
    return self.proxy.get_account_info(self.auth)
    
  def get_public_key(self):
    return self.proxy.get_public_key(self.auth)
      
  def get_private_key(self):
    return self.proxy.get_private_key(self.auth)
      
  def delete_private_key(self):
    try:
      self.proxy.delete_private_key(self.auth)
    except xmlrpclib.Fault, fault:
      if 'Fault 104' in str(fault):
        raise GENI_KeyAlreadyRemoved
      else:
        print(str(fault))

class GENI_AuthError(Exception):
  def __init__(self, value=None):
    self.value = "GENI Exception: Authentication Error."
  def __str__(self):
    return repr(self.value)

class GENI_NotEnoughCredits(Exception):
  def __init__(self, value=None):
    self.value = "GENI Exception: Not enough credits to acquire resources."
  def __str__(self):
    return repr(self.value)

class GENI_NoAvailNodes(Exception):
  def __init__(self, value=None):
    self.value = "GENI Exception: No available nodes to acquire."
  def __str__(self):
    return repr(self.value)

class GENI_KeyAlreadyRemoved(Exception):
  def __init__(self, value=None):
    self.value = "GENI Exception: Private key already removed."
  def __str__(self):
    return repr(self.value)

class GENI_OpError(Exception):
  def __init__(self, value=None):
    self.value = value
  def __str__(self):
    return repr(self.value)    
