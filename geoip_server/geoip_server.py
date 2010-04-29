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
  geoip_server.py /path/to/GeoIP.dat

  Where /path/to/GeoIP.dat is the path to a legal GeoIP database. Databases can
  be downloaded at http://www.maxmind.com/app/ip-location.

  More information on pygeoip at http://code.google.com/p/pygeoip/.
"""

import sys
sys.path.append("./seattle/seattle_repy")
import pygeoip
import repyportability
from SimpleXMLRPCServer import SimpleXMLRPCServer

# Handle arguments
if len(sys.argv) < 2:
    print "Error: Please specify the filename of a valid GeoIP datebase."
    raise RuntimeError

geoipdb_filename = sys.argv[1]

# Get external IP
ext_ip = repyportability.getmyip()

# Create server
server = SimpleXMLRPCServer((ext_ip, 12679), allow_none=True)

# Initialize and register geoip object
gic = pygeoip.GeoIP(geoipdb_filename)
server.register_instance(gic)

# Run the server's main loop
server.serve_forever()
