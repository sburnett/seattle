"""
Example of using the seattleclearinghouse_xmlrpc module's SeattleGENIClient.

This script tries to acquire, renew, and release some vessels and prints out
various information along the way.
"""


import sys
import subprocess

LOCAL = False

if LOCAL:
  USERNAME = "angela"
  DEFAULT_XMLRPC_URL = "http://blackbox.cs.washington.edu:8001/xmlrpc/"
  API_KEY = "R2J1QXZ604M9HWBIKF3G8CLDP5A7UYTN"
else:
  USERNAME = "danny"
  DEFAULT_XMLRPC_URL = "https://seattlegeni.cs.washington.edu/xmlrpc/"
  API_KEY = "GMCIB70LY4963RNU15PQHFXDEZ2T8WKJ"


# Allowing SSL to be insecure means it will be susceptible to MITM attacks.
# See the instructions in seattleclearinghouse_xmlrpc.py for using SSL securely.
ALLOW_SSL_INSECURE = True


def do_example_acquire_renew_release():
  client = SeattleGENIClient(username=USERNAME,
                             api_key=API_KEY,
                             allow_ssl_insecure=ALLOW_SSL_INSECURE)

  try:
    f = open('nodeman.cfg')
    dictobj = eval(f.read())
    f.close()
  except Exception, e:
    print "addme.py: unable to read public key: '%s'" % e
    return

  publickey = dictobj['publickey']
  keystr = "%s %s" % (publickey['e'], publickey['n'])
  print "(%s)" % keystr
  vesselcount = 0
  maxvessels = 2
  try:
    maxvessels = int(sys.argv[1])
  except:
    pass


  # # pass the correct vessel info

  # if LOCAL:
  #   print shellrun('cp vesselinfo_emily ../nm/seattle_repy')
  # else:
  #   print shellrun('cp vesselinfo_danny ../nm/seattle_repy')


  # acquire vessel!

  v = 2
  while v < 10:
    v += 2

    try:
      if vesselcount >= maxvessels:
        break
      handle = "%s:v%d" % (keystr, v)
      new_vessel = client.acquire_specific_vessels([handle])
      if not new_vessel:
        print "addme.py: v%d already added" % v
      vesselcount += 1
    except Exception, e:
      print "Error in adding v%d." % (v)
    
  print "addme.py: %d vessels started (max=%d)." % (vesselcount,maxvessels)




def main():
  do_example_acquire_renew_release()



def shellrun(cmd):
  proc = subprocess.Popen(cmd, shell=True,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE)
  return proc.communicate()[0]





"""
<Program>
  seattleclearinghouse_xmlrpc.py

<Started>
  6/28/2009

<Author>
  Jason Chen
  Justin Samuel

<Purpose>
  A client library for communicating with the SeattleGENI XMLRPC Server.
  
  Your Python scripts can import this library, create an instance of the
  SeattleGENIClient class, then call methods on the object to perform XMLRPC
  calls through the SeattleGENI XMLRPC API.

  Full tutorials on using this library, see:
  https://seattle.cs.washington.edu/wiki/SeattleGeniClientLib
  
  In order to perform secure SSL communication with SeattleGENI:
    * You must have M2Crypto installed.
    * You must set the value of CA_CERTIFICATES_FILE to the location of a PEM
      file containing CA certificates that you trust. If you don't know where
      this is on your own system, you can download this file from a site you
      trust. One such place to download this file from is:
        http://curl.haxx.se/ca/cacert.pem
        
  If you can't fulfill the above requirements, you can still use this client with
  XMLRPC servers that use https but you will be vulnerable to a man-in-the-middle
  attack. To enable this insecure mode, include the argument:
    allow_ssl_insecure=True
  when creating a SeattleGENIClient instance.
  
<Notes>
  All methods of the client class may raise the following errors in addition to
  any others described in the method's docstring:
    CommunicationError
    AuthenticationError
    InvalidRequestError
    InternalError
  The safest way to be certain to catch any of these errors  is to the catch
  their base class:
    SeattleGENIError
    
<Version>
  $Rev: 3841 $ ($Date: 2010-04-27 10:43:39 -0700 (Tue, 27 Apr 2010) $)
"""

import os
import socket
import xmlrpclib


# Location of a file containing one or more PEM-encoded CA certificates
# concatenated together. This is required if using allow_ssl_insecure=False.
# By default it looks for a cacert.pem file in the same directory as this
# python module is in.
DEFAULT_CA_CERTIFICATES_FILE = os.path.join(os.path.dirname(__file__), "cacert.pem")

# SeattleGENI XMLRPC Fault Code Constants
FAULTCODE_INTERNALERROR = 100
FAULTCODE_AUTHERROR = 101
FAULTCODE_INVALIDREQUEST = 102
FAULTCODE_NOTENOUGHCREDITS = 103
FAULTCODE_UNABLETOACQUIRE = 105



class SeattleGENIClient(object):
  """
  Implementation of an XMLRPC client for communicating with a SeattleGENI
  server. This uses the public API described at:
  https://seattle.cs.washington.edu/wiki/SeattleGeniAPI
  """
  
  def __init__(self, username, api_key=None, private_key_string=None,
               xmlrpc_url=None,
               allow_ssl_insecure=None,
               ca_certs_file=None):
    
    if xmlrpc_url is None:
      xmlrpc_url = DEFAULT_XMLRPC_URL
      
    if allow_ssl_insecure is None:
      allow_ssl_insecure = False
      
    if ca_certs_file is None:
      ca_certs_file = DEFAULT_CA_CERTIFICATES_FILE
    
    if not isinstance(username, basestring):
      raise TypeError("username must be a string")
    
    if api_key is not None:
      if not isinstance(api_key, basestring):
        raise TypeError("api_key must be a string")
    else:
      if not private_key_string:
        raise TypeError("private_key_string must be provided if api_key is not")
      if not isinstance(private_key_string, basestring):
        raise TypeError("private_key_string must be a string")
      
    if not isinstance(xmlrpc_url, basestring):
      raise TypeError("xmlrpc_url must be a string")
    if not isinstance(allow_ssl_insecure, bool):
      raise TypeError("allow_ssl_insecure must be True or False")
    if not isinstance(ca_certs_file, basestring):
      raise TypeError("ca_certs_file must be a string")
    
    if allow_ssl_insecure:
      self.proxy = xmlrpclib.Server(xmlrpc_url)
    else:
      ssl_transport = _get_ssl_transport(ca_certs_file)
      self.proxy = xmlrpclib.Server(xmlrpc_url, transport=ssl_transport)

    if not api_key:
      api_key = self._get_api_key(username, private_key_string)
    
    self.auth = {'username':username, 'api_key':api_key}



  def _get_api_key(self, username, private_key_string):
    # Normally we try not to import modules anywhere but globally,
    # but I'd like to keep this xmlrpc client usable without repy files
    # available when the user provides their api key and doesn't require
    # it to be retrieved.
    try:
      import repyhelper
      import repyportability
      repyhelper.translate_and_import("rsa.repy")
    except ImportError, e:
      raise SeattleGENIError("Unable to get API key from SeattleGENI " +
                             "because a required python or repy module " + 
                             "cannot be found:" + str(e))
    
    # This will raise a ValueError if the private key is not valid.
    private_key_dict = rsa_string_to_privatekey(private_key_string)
    
    encrypted_data = self.proxy.get_encrypted_api_key(username)
    decrypted_data = rsa_decrypt(encrypted_data, private_key_dict)
    split_data = decrypted_data.split("!")

    # The encrypted data has 20 bytes of random data followed by a "!" which
    # is then followed by the actual API key. If the private key was the wrong
    # key, we will end up with garbage data (if it was an invalid key, it
    # might be empty, though). So, we're going to make the fairly safe
    # assumption that the odds of a random decryption with the wrong key
    # resulting in data that starts with 20 bytes which aren't exclamation
    # marks followed by a single exclamation mark and no others is pretty low.
    if len(split_data) != 2 or len(split_data[0]) != 20:
      raise AuthenticationError("The provided private key does not appear " +
                                "to correspond to this account's public key: " +
                                "encrypted API key could not be decrypted.")
    api_key = split_data[1]
    
    return api_key


  
  def _do_call(self, function, *args):
    try:
      return function(self.auth, *args)
    except socket.error, err:
      raise CommunicationError("XMLRPC failed: " + str(err))
    except xmlrpclib.Fault, fault:
      if fault.faultCode == FAULTCODE_AUTHERROR:
        raise AuthenticationError
      elif fault.faultCode == FAULTCODE_INVALIDREQUEST:
        raise InvalidRequestError(fault.faultString)
      elif fault.faultCode == FAULTCODE_NOTENOUGHCREDITS:
        raise NotEnoughCreditsError(fault.faultString)
      elif fault.faultCode == FAULTCODE_UNABLETOACQUIRE:
        raise UnableToAcquireResourcesError(fault.faultString)
      else:
        raise InternalError(fault.faultString)



  def _do_pwauth_call(self, function, password, *args):
    """For use by calls that require a password rather than an api key."""
    pwauth = {'username':self.auth['username'], 'password':password}
    try:
      return function(pwauth, *args)
    except socket.error, err:
      raise CommunicationError("XMLRPC failed: " + str(err))
    except xmlrpclib.Fault, fault:
      if fault.faultCode == FAULTCODE_AUTHERROR:
        raise AuthenticationError
      elif fault.faultCode == FAULTCODE_INVALIDREQUEST:
        raise InvalidRequestError(fault.faultString)
      elif fault.faultCode == FAULTCODE_NOTENOUGHCREDITS:
        raise NotEnoughCreditsError(fault.faultString)
      elif fault.faultCode == FAULTCODE_UNABLETOACQUIRE:
        raise UnableToAcquireResourcesError(fault.faultString)
      else:
        raise InternalError(fault.faultString)



  def acquire_lan_resources(self, count):
    """
    <Purpose>
      Acquire LAN vessels.
    <Arguments>
      count
        The number of vessels to acquire.
    <Exceptions>
      The common exceptions described in the module comments, as well as:
      SeattleGENINotEnoughCredits
        If the account does not have enough available vessel credits to fulfill
        the request.
    <Side Effects>
      If successful, 'count' LAN vessels have been acquired for the account.
    <Returns>
      A list of vessel handles of the acquired vessels.
    """
    return self.acquire_resources('lan', count)



  def acquire_wan_resources(self, count):
    """
    <Purpose>
      Acquire WAN vessels.
    <Arguments>
      count
        The number of vessels to acquire.
    <Exceptions>
      The common exceptions described in the module comments, as well as:
      SeattleGENINotEnoughCredits
        If the account does not have enough available vessel credits to fulfill
        the request.
    <Side Effects>
      If successful, 'count' WAN vessels have been acquired for the account.
    <Returns>
      A list of vessel handles of the acquired vessels.
    """
    return self.acquire_resources('wan', count)



  def acquire_nat_resources(self, count):
    """
    <Purpose>
      Acquire NAT vessels.
    <Arguments>
      count
        The number of vessels to acquire.
    <Exceptions>
      The common exceptions described in the module comments, as well as:
      SeattleGENINotEnoughCredits
        If the account does not have enough available vessel credits to fulfill
        the request.
    <Side Effects>
      If successful, 'count' NAT vessels have been acquired for the account.
    <Returns>
      A list of vessel handles of the acquired vessels.
    """
    return self.acquire_resources('nat', count)



  def acquire_random_resources(self, count):
    """
    <Purpose>
      Acquire vessels (they can be LAN, WAN, NAT, or any combination of these).
    <Arguments>
      count
        The number of vessels to acquire.
    <Exceptions>
      The common exceptions described in the module comments, as well as:
      SeattleGENINotEnoughCredits
        If the account does not have enough available vessel credits to fulfill
        the request.
    <Side Effects>
      If successful, 'count' vessels have been acquired for the account.
    <Returns>
      A list of vessel handles of the acquired vessels.
    """
    return self.acquire_resources('random', count)
    
    
    
  def acquire_resources(self, res_type, count):
    """
    <Purpose>
      Acquire vessels.
    <Arguments>
      res_type
        A string describing the type of vessels to acquire.
      count
        The number of vessels to acquire.
    <Exceptions>
      The common exceptions described in the module comments, as well as:
      SeattleGENINotEnoughCredits
        If the account does not have enough available vessel credits to fulfill
        the request.
    <Side Effects>
      If successful, 'count' vessels have been acquired for the account.
    <Returns>
      A list of vessel handles of the acquired vessels.
    """
    if not isinstance(res_type, basestring):
      raise TypeError("res_type must be a string")
    if type(count) not in [int, long]:
      raise TypeError("count must be an integer")
    
    rspec = {'rspec_type':res_type, 'number_of_nodes':count}
    return self._do_call(self.proxy.acquire_resources, rspec)



  def acquire_specific_vessels(self, handlelist):
    """
    <Purpose>
      Attempt to acquire specific vessels.
    <Arguments>
      handlelist
        A list of vessel handles.
    <Exceptions>
      The common exceptions described in the module comments, as well as:
      SeattleGENINotEnoughCredits
        If the account does not have enough available vessel credits to fulfill
        the request.
    <Side Effects>
      If successful, zero or more vessels from handlelist have been acquired.
    <Returns>
      A list of vessel handles of the acquired vessels.
    """
    _validate_handle_list(handlelist)
    return self._do_call(self.proxy.acquire_specific_vessels, handlelist)



  def release_resources(self, handlelist):
    """
    <Purpose>
      Release vessels.
    <Arguments>
      handlelist
        A list of handles as returned by acquire_vessels() or found in the
        'handle' key of the dictionaries returned by get_resource_info().
    <Exceptions>
      The common exceptions described in the module comments.
    <Side Effects>
      If successful, the vessels in handlelist have been released. If not
      successful, it is possible that a partial set of the vessels was
      released.
    <Returns>
      None
    """
    _validate_handle_list(handlelist)
    return self._do_call(self.proxy.release_resources, handlelist)

      
      
  def renew_resources(self, handlelist):
    """
    <Purpose>
      Renew vessels.
    <Arguments>
      handlelist
        A list of handles as returned by acquire_vessels() or found in the
        'handle' key of the dictionaries returned by get_resource_info().
    <Exceptions>
      The common exceptions described in the module comments, as well as:
      SeattleGENINotEnoughCredits
        If the account is currently over its vessel credit limit, then vessels
        cannot be renewed until the account is no longer over its credit limit.
    <Side Effects>
      If successful, the vessels in handlelist have been renewed. If not
      successful, it is possible that a partial set of the vessels was
      renewed.
    <Returns>
      None
    """
    _validate_handle_list(handlelist)
    return self._do_call(self.proxy.renew_resources, handlelist)
    


  def get_resource_info(self):
    """
    <Purpose>
      Obtain information about acquired vessels.
    <Arguments>
      None
    <Exceptions>
      The common exceptions described in the module comments, as well as:
    <Side Effects>
      None
    <Returns>
      A list of dictionaries, where each dictionary describes a vessel that
      is currently acquired by the account.
    """
    return self._do_call(self.proxy.get_resource_info)
      
      
      
  def get_account_info(self):
    """
    <Purpose>
      Obtain information about the account.
    <Arguments>
      None
    <Exceptions>
      The common exceptions described in the module comments, as well as:
    <Side Effects>
      None
    <Returns>
      A dictionary with information about the account.
    """
    return self._do_call(self.proxy.get_account_info)
    
    
    
  def get_public_key(self):
    """
    <Purpose>
      Obtain the public key of the account.
    <Arguments>
      None
    <Exceptions>
      The common exceptions described in the module comments, as well as:
        None
    <Side Effects>
      None
    <Returns>
      A string containing the public key of the account.
    """
    return self._do_call(self.proxy.get_public_key)



  def set_public_key(self, password, pubkeystring):
    """
    <Purpose>
      Set the public key of the account.
    <Arguments>
      password
        The account password. This is required because changing the public
        key of the account cannot be done with just the api key.
      pubkeystring
        A string representing the new public key to be set for the account.
    <Exceptions>
      The common exceptions described in the module comments, as well as:
        InvalidRequestError
          If the pubkey is invalid.
    <Side Effects>
      The public key of the account is changed and will be updated on all
      vessels the account has acquired.
    <Returns>
      None
    """
    self._do_pwauth_call(self.proxy.set_public_key, password, pubkeystring)



  def regenerate_api_key(self, password):
    """
    <Purpose>
      Generate a new API key for the account..
    <Arguments>
      password
        The account password. This is required because changing the api
        key of the account cannot be done with just the current api key.
    <Exceptions>
      The common exceptions described in the module comments, as well as:
        None
    <Side Effects>
      The account's api key has been changed.
    <Returns>
      The new api key for the account.
    """
    api_key = self._do_pwauth_call(self.proxy.regenerate_api_key, password)
    self.auth['api_key'] = api_key
    return api_key
   
      


def _validate_handle_list(handlelist):
  """
  Raise a TypeError or ValueError if handlelist is not a non-empty list of
  string.
  """
  if not isinstance(handlelist, list):
    raise TypeError("Invalid data type for handle list: " + 
                    str(type(handlelist)))
  
  for handle in handlelist:
    if not isinstance(handle, basestring):
      raise TypeError("Invalid data type for a handle in the handle list: " + 
                      str(type(handle)))
  
  if not handlelist:
    raise ValueError("Given handlelist is empty.")





def _get_ssl_transport(ca_certs_file):
  """
  Returns an object usable as the transport for an xmlrpclib proxy. This will
  be an M2Crypto.m2xmlrpclib.SSL_Transport that has been configured with a
  context that has the ca_certs_file loaded, will not allow SSLv2, and will
  reject certificate names that don't match the hostname.
  """
  try:
    import M2Crypto
  except ImportError, err:
    raise ImportError("In order to use the SeattleGENI XMLRPC client with " + 
                      "allow_ssl_insecure=False, you need M2Crypto " + 
                      "installed. " + str(err))
  
  # We don't define this class until here because otherwise M2Crypto may not
  # be available.
  class M2CryptoSSLTransport(M2Crypto.m2xmlrpclib.SSL_Transport):
    def request(self, host, handler, request_body, verbose=0):
      if host.find(":") == -1:
        host = host + ":443"
      return M2Crypto.m2xmlrpclib.SSL_Transport.request(self, host, handler,
                                                        request_body, verbose)

  ctx = M2Crypto.SSL.Context("sslv3")
  ctx.set_verify(M2Crypto.SSL.verify_peer | 
                 M2Crypto.SSL.verify_fail_if_no_peer_cert, depth=9)
  if ctx.load_verify_locations(ca_certs_file) != 1:
    raise SeattleGENIError("No CA certs found in file: " + ca_certs_file)

  return M2CryptoSSLTransport(ctx)





class SeattleGENIError(Exception):
  """Base class for exceptions raised by the SeattleGENIClient."""
  

class CommunicationError(SeattleGENIError):
  """
  Indicates that XMLRPC communication failed.
  """
  
  
class InternalError(SeattleGENIError):
  """
  Indicates an unexpected error occurred, probably either a bug in this
  client or a bug in SeattleGENI.
  """


class AuthenticationError(SeattleGENIError):
  """Indicates an authentication failure (invalid username and/or API key)."""
  def __init__(self, msg=None):
    if msg is None:
      msg = "Authentication failed. Invalid username and/or API key."
    SeattleGENIError.__init__(self, msg)


class InvalidRequestError(SeattleGENIError):
  """Indicates that the request is invalid."""


class NotEnoughCreditsError(SeattleGENIError):
  """
  Indicates that the requested operation requires more vessel credits to
  be available then the account currently has.
  """
  
  
class UnableToAcquireResourcesError(SeattleGENIError):
  """
  Indicates that the requested operation failed because SeattleGENI was unable
  to acquire the requested resources.
  """







if __name__ == "__main__":
  main()
