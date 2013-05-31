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
from SimpleXMLRPCServer import SimpleXMLRPCServer

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
gic = pygeoip.GeoIP(geoipdb_filename)
server.register_instance(gic)

# Run the server's main loop
server.serve_forever()
