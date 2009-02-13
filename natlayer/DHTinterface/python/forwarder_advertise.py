import advertise
import threading
import misc
import random

# The frequency of updating the advertisements
adfrequency = 300

# the TTL of those adverts
adTTL = 750


class fadvertthread(threading.Thread):
	key = None
	forwarderip = None

	def __init__(self, forwarderip, key):
		self.key = key
		self.forwarderip = forwarderip
		threading.Thread.__init__(self, name = "Forwarder Advertisement Thread")
		
	def run(self):
		while True:
			#print "Hello World"
			advertise.announce(self.key, self.forwarderip, adTTL)
			
			#centralizedadvertise_announce(self.key, self.forwarderip, adTTL)
			car =  raw_input("car name: ")
			misc.do_sleep(30)
			
			
def flookup(maxvals = 100):
	flist = advertise.lookup('forwarder')
	a = random.randint(1, 1000)
	index = a % len(flist)
	return flist[index]
