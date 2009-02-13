import advertise
import threading
import misc

# The frequency of updating the advertisements
adfrequency = 300

# the TTL of those adverts
adTTL = 750

#two variables: unique key (e.g. mac address), ip address of current forwarder

mycontext['forwarderip'] = None

class sadvertthread(threading.Thread):
	key = None #the key will be something unique, e.g. user mac address
	forwarderip = None

	def __init__(self, fip, key):
		self.key = key
		self.forwarderip = fip
		threading.Thread.__init__(self, name = "Server Advertisement Thread")
		
	def run(self):
		while True:
			advertise.announce(self.key, self.forwarderip, adTTL)
			
			car =  raw_input("server ")

			
			misc.do_sleep(30)

def slookup(key, maxvals = 100):
	currforwarder = advertise.lookup(key)
	return currforwarder
	