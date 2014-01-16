#!/usr/bin/env python
"""
<Author>
  Evan Meagher

<Start Date>
  Nov 26, 2009

<Description>
  Starts an XML-RPC server that allows remote clients to execute geolocation
  queries using the pygeoip library.

<Usage>
  python geoip_server.py /path/to/GeoIP.dat PORT

  Where /path/to/GeoIP.dat is the path to a legal GeoIP database and PORT is
  the port on which to host the server. Databases can be downloaded at
  http://www.maxmind.com/app/ip-location.

  More information on pygeoip at http://code.google.com/p/pygeoip/.
  More information on geoip_server.py at
  http://seattle.poly.edu/wiki/GeoIPServer
"""

import sys
sys.path.append("./seattle/seattle_repy")
import pygeoip
import repyportability
import xmlrpclib
from SimpleXMLRPCServer import SimpleXMLRPCServer


class SafeGeoIPServer(pygeoip.GeoIP):
  """
  <Purpose>
    Provides safe wrappers around the GeoIP server method calls.
    This allows us to check that each request is well-formatted before
    executing them on pygeoip.

    This class does not introduce any new methods; it only overrides
    existing methods in pygeoip.GeoIP.

  """
  def record_by_addr(self, addr):
    """
    <Purpose>
      Returns the GeoIP record for the specified IP address.

    <Arguments>
      addr: A public IPv4 address.

    <Side Effects>
      None

    <Exceptions>
      None

    <Return>
      A dictionary containing GeoIP information for the address
      specified, if valid.
      Returns False on errors.
    """
    if not _is_public_ipv4(addr):
      return xmlrpclib.Fault(xmlrpclib.INVALID_METHOD_PARAMS, "Not a public IP address")

    return super(SafeGeoIPServer, self).record_by_addr(addr)


def _is_public_ipv4(addr):
  """
  <Purpose>
    Determines if an IPv4 address is public or not.

  <Arguments>
    addr: An IPv4 address.

  <Side Effects>
    None

  <Exceptions>
    None, assuming that the provided value is a valid IPv4 address.

  <Returns>
    True if it is a public IP address, False otherwise.
  """
  # We need to do some range comparisons for Class B and C addresses,
  # so preprocess them into ints.
  ip_int_tokens = [int(token) for token in addr.split('.')]
  if ip_int_tokens[0] == 10:
    # Class A private address is in the form 10.*.*.*
    return False
  # Class B private addresses are in the range 172.16.0.0/16 to
  # 172.31.255.255/16
  elif ip_int_tokens[0] == 172:
    if 16 <= ip_int_tokens[1] and ip_int_tokens[1] < 32:
      return False
  # Class C private addresses are in the form 192.168.*.*
  elif ip_int_tokens[0:2] == [192, 168]:
    return False
  return True


# Handle arguments
if len(sys.argv) < 3:
    print "Usage: python geoip_server.py /path/to/GeoIP.dat PORT"
    raise RuntimeError

geoipdb_filename = sys.argv[1]
port = int(sys.argv[2])

# Get external IP
ext_ip = repyportability.getmyip()

# Create server
server = SimpleXMLRPCServer((ext_ip, port), allow_none=True)

# Initialize and register geoip object
gic = SafeGeoIPServer(geoipdb_filename)
server.register_instance(gic)

# Run the server's main loop
server.serve_forever()
