"""
Program Name: test_seattlegeni_xmlrpc.py
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
certificate_file = "/home/monzum/temp/emulab.pem"
certificate_key = "/home/monzum/temp/emulab.pem"
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
     <owner_urn>urn:publicid:IDN+emulab.net+user+monzum</owner_urn>
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
MIIDRTCCAq4CAloQMA0GCSqGSIb3DQEBBAUAMIG4MQswCQYDVQQGEwJVUzENMAsG
A1UECBMEVXRhaDEXMBUGA1UEBxMOU2FsdCBMYWtlIENpdHkxHTAbBgNVBAoTFFV0
YWggTmV0d29yayBUZXN0YmVkMR4wHAYDVQQLExVDZXJ0aWZpY2F0ZSBBdXRob3Jp
dHkxGDAWBgNVBAMTD2Jvc3MuZW11bGFiLm5ldDEoMCYGCSqGSIb3DQEJARYZdGVz
dGJlZC1vcHNAZmx1eC51dGFoLmVkdTAeFw0xMDA2MDMxODIxMTJaFw0xMzAyMjcx
ODIxMTJaMIGgMQswCQYDVQQGEwJVUzENMAsGA1UECBMEVXRhaDEdMBsGA1UEChMU
VXRhaCBOZXR3b3JrIFRlc3RiZWQxEjAQBgNVBAsTCXNzbHhtbHJwYzEtMCsGA1UE
AxMkYWE2NDNkM2ItNmYzYi0xMWRmLWFkODMtMDAxMTQzZTQ1M2ZlMSAwHgYJKoZI
hvcNAQkBFhFtb256dW1AZW11bGFiLm5ldDCBnzANBgkqhkiG9w0BAQEFAAOBjQAw
gYkCgYEAw2SkbRcdOLawqp76+R9FgUE4FlVi7mVd2FTxuYBqsDsE+ALT5uAhYSyd
bgHKdhfP8DDau2+PD1K0iRckzNUCLiVo9Lwx+7gLasP/R7Yriq0UfGCxWQqkGHUd
kKJ8NVbN+yFo/HqQOsVYeQ1kdOyAcQpDdz81CGnkSYAX/LOBQlUCAwEAAaN5MHcw
DwYDVR0TAQH/BAUwAwEB/zAdBgNVHQ4EFgQUI5kJWJaukxRKbSeZqhBbvngJeSYw
RQYDVR0RBD4wPIYndXJuOnB1YmxpY2lkOklETitlbXVsYWIubmV0K3VzZXIrbW9u
enVtgRFtb256dW1AZW11bGFiLm5ldDANBgkqhkiG9w0BAQQFAAOBgQASWi7CbSl9
Zw0A83XFEaeKLcUvugSZawPKL0dRbp0pAfWYsMe99wYO0TPay8iPDWIXxkzwPcEX
e9zv1ROqcQalbK1Ej/LkoA437WfxKufjM7rOXFEMePUpNHR+OFQRbIcDvit9/UTi
svR3URQ1J91IPasDJRD2lDGWXV+A5gKY7Q==
-----END CERTIFICATE-----</signatures>
</signed-credential>"""
    #  print protogeni_credential
    
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
