"""
Program Name: test_seattleclearinghouse_xmlrpc.py
Author: Monzur Muhammad
Created: May 25, 2010
"""

import xmlrpclib
import traceback


from M2Crypto.m2xmlrpclib import SSL_Transport
from M2Crypto import SSL
from M2Crypto import X509

from urlparse import urlsplit, urlunsplit
from urllib import splitport



server_address = "https://blackbox.cs.washington.edu:443/xmlrpc/"
certificate_file = "/path/to/certificate/emulab.pem"
certificate_key = "/path/to/certificate/emulab.pem"
slice_urn = "urn:publicid:IDN+SeattleGENI+slice+mytestslice"

CREATE_SLIVER = False

ssl_certificate = X509.load_cert(certificate_file)

def load_ssl():
  """
  <Purpose>
    Load the ssl files that will be used for the xmlrpc communication.
  
  <Argument>
    None

  <Side Effects>
    None

  <Return>
    The ssl context.
  """

  ssl_context = SSL.Context("sslv23")
  ssl_context.load_cert(certificate_file, certificate_key)
  ssl_context.set_verify(SSL.verify_none, 16)
  ssl_context.set_allow_unknown_ca(0)
 
  return ssl_context



def test_create_sliver(server, protogeni_credential, slice_num):

  create_sliver_arg = {'slice_urn' : slice_urn+slice_num,
                       'rspec' : str(1+int(slice_num)),
                       'credentials': (protogeni_credential,)}

  try:
    result = server.CreateSliver(create_sliver_arg)

    if type(result['value']).__name__ == 'dict':
      print result['value']['sliver']
      print result['value']['manifest']
    else:
      print result

  except Exception, e:
    print str(traceback.format_exc())





def test_delete_slice(server, protogeni_credential, slice_num):

  delete_slice_arg = {'slice_urn' : slice_urn+slice_num,
                      'credentials': (protogeni_credential,)}

  try:
    print server.DeleteSlice(delete_slice_arg)
  except Exception, e:
    print str(traceback.format_exc())





def main():

  ssl_context = load_ssl()
  server = xmlrpclib.ServerProxy(server_address, SSL_Transport(ssl_context), verbose=0)
  

  # Open up the certificate file  
  cert_file_handle = open(certificate_file)
  protogeni_credential_part1 = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
   <signed-credential>
    <credential xml:id="ref1">
     <type>privilege</type>
     <serial>12345</serial>
     <owner_urn>urn:publicid:IDN+emulab.net+user+test_user</owner_urn>
     <target_urn>urn:publicid:IDN+SeattleGENI+slice+mytestslice"""
  protogeni_credential_part2 = """</target_urn>
     <expires>2010-01-01T00:00:00</expires>
     <privileges>
      <privilege>
       <name>*</name>
       <can_delegate>1</can_delegate>
      </privilege>
     </privileges>
    </credential>
    <signatures>-----BEGIN CERTIFICATE-----
########The emulab certificate for a user.#########
-----END CERTIFICATE-----</signatures>
</signed-credential>"""

    
  for i in range(3):
    test_create_sliver(server, protogeni_credential_part1+str(i)+protogeni_credential_part2, str(i))
 
  for i in range(3):
    test_create_sliver(server, protogeni_credential_part1+str(i)+protogeni_credential_part2, str(i))
  
  for i in range(3):
    test_delete_slice(server, protogeni_credential_part1+str(i)+protogeni_credential_part2, str(i))
 
  for i in range(3):
    test_delete_slice(server, protogeni_credential_part1+str(i)+protogeni_credential_part2, str(i))


if __name__ == "__main__":
  main()
