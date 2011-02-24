"""
<Program Name>
  example_single_build.py

<Started>
  September 2010

<Author>
  Alex Hanson

<Purpose>
  Sends an XML-RPC request to the given URL to create a custom installer
  for Linux, Mac, and Windows.
"""

import sys
import xmlrpclib
from time import time


def main(url):
  proxy = xmlrpclib.ServerProxy(url)
  
  vessels = [
    {'percentage': 60, 'owner': 'alex', 'users': ['bob']},
    {'percentage': 20, 'owner': 'carl', 'users': ['darren']},
  ]
    
  user_data = {
    'alex': {'public_key': '12345 54321'},
    'darren': {'public_key': '67890 09876'},
  }
  
  print 'Initiating a single custom installer request...'
  
  start = time()
  results = proxy.build_installers(vessels, user_data)
  end = time()
  
  time_ellapsed = end - start
  
  print 'Installer was built in ' + str(time_ellapsed) + ' seconds. Results:\n'
  print results

   
if __name__ == '__main__':
  if len(sys.argv) != 2:
    print 'Usage: ' + sys.argv[0] + ' <XML-RPC URL>'
  else:
    main(sys.argv[1])
