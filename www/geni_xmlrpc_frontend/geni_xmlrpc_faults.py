"""
<Program Name>
  geni_xmlrpc_faults.py

<Started>
  6/28/2009

<Author>
  Jason Chen
  jchen@cs.washington.edu

<Purpose>
  Defines GENI customized XMLRPC Fault classes, to be raised when
  an error on the geni_xmlrpc_server occurs. These custom faults are
  sent over the wire to XMLRPC clients, who should refer to the XMLRPC API
  to determine what the various raised fault codes actually mean.
"""

import xmlrpclib

class GENIFault(xmlrpclib.Fault):
  def __init__(self, faultCode, faultString):
    xmlrpclib.Fault.__init__(self, faultCode, faultString)

class GENI_OpError(GENIFault):
  def __init__(self, info = None):
    faultString = "GENI XMLRPC Fault (GENI_OpError): Internal error. Details: "
    if info:
      faultString += info
    else:
      faultString += "(none)"
    GENIFault.__init__(self, 100, faultString)

class GENI_AuthError(GENIFault):
  def __init__(self):
    faultString = "GENI XMLRPC Fault (GENI_AuthError): Couldn't authenticate user."
    GENIFault.__init__(self, 101, faultString)


class GENI_NotEnoughCredits(GENIFault):
  def __init__(self):
    faultString = "GENI XMLRPC Fault (GENI_NotEnoughCredits): Not enough credits to acquire requested resources."
    GENIFault.__init__(self, 102, faultString)

class GENI_NoAvailNodes(GENIFault):
  def __init__(self):
    faultString = "GENI XMLRPC Fault (GENI_NoAvailNodes): No available nodes to acquire."
    GENIFault.__init__(self, 103, faultString)
    
class GENI_KeyAlreadyRemoved(GENIFault):
  def __init__(self):
    faultString = "GENI XMLRPC Fault (GENI_KeyAlreadyRemoved): Private key already removed."
    GENIFault.__init__(self, 104, faultString)
    

