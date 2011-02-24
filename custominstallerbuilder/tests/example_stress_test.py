"""
<Program Name>
  example_stress_test.py

<Started>
  September 2010

<Author>
  Alex Hanson

<Purpose>
  Splits into ten threads, each of which poses an XML-RPC request to the given
  URL for an indentical installer. In this way, one can get a sense for how
  long it takes to build many installers.
"""

import sys
import xmlrpclib
from threading import Thread
from time import time

      
class Agent(Thread):        
  def __init__(self, url, count):
    self.url = url
    self.count = count
    super(Agent, self).__init__()

  def run(self):
    proxy = xmlrpclib.ServerProxy(self.url)
    
    vessels = [
      {'percentage': 60, 'owner': 'alex', 'users': ['bob']},
      {'percentage': 20, 'owner': 'carl', 'users': ['darren']},
    ]

    user_data = {
      'alex': {'public_key': '12345 54321'},
      'darren': {'public_key': '67890 09876'},
    }
    
    start = time()
    results = proxy.build_installers(vessels, user_data)
    end = time()
    
    self.time_ellapsed = end - start


def main(url, count):
  agents = list()
  time_ellapsed = list()
  
  print 'Initiating ' + str(count) + ' installer requests...'
  
  for x in range(count):
    agent = Agent(url, x)
    agent.start()
    agents.append(agent)
    
  print 'Waiting on all builds to finish...'
        
  for agent in agents:
    agent.join()
    time_ellapsed.append(agent.time_ellapsed)
  
  average_time = float(sum(time_ellapsed)) / len(time_ellapsed)
  
  print ('The ' + str(count) + ' installers took ' + str(average_time) +
         ' seconds on average to build.')
    
    
if __name__ == '__main__':
  if len(sys.argv) != 2:
    print 'Usage: ' + sys.argv[0] + ' <XML-RPC URL>'
  else:
    main(sys.argv[1], 50)
