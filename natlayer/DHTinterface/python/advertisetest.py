# the last time the thread was started
thread_starttime = {}

# the time I should wait
thread_waittime = {}

# never wait more than 5 minutes
maxwaittime = 300.0

# or less than 2 seconds
minwaittime = 2.0

# multiply by 1.5 each time...
wait_exponent = 1.5

# and start to decrease only after a reasonable run time...
reasonableruntime = 30

# and drop by
decreaseamount = .5


#advertisetest

# this is called when the thread is started...
def started_waitable_thread(threadid):
  thread_starttime[threadid] = time.time()
  thread_waittime[threadid] = min(maxwaittime, thread_waittime[threadid] ** wait_exponent)


import time

import threading

import nmadvertise

import nmstatusmonitor

import nmconnectionmanager

import nmrequesthandler

import persist

import misc

import runonce

import nonportable 

import forwarder_advertise

import server_advertise

import advertise

fadvert = forwarder_advertise.fadvertthread('255.0.0.0', 'forwarder')
#fadvert.setDaemon(True)
fadvert.start()

sadvert = server_advertise.sadvertthread('6.0.0.0' , 'mac address') #should be mycontext dictionary
#started_waitable_thread('fadvert')
sadvert.start()

#mycontext['ip'] = None
#mycontext['ip2'] = None
#mycontext['sip'] = None

ip = None
ip2 = None
sip = None
while True:
	print "hello world"
	print ip
	print ip2
	print sip
	misc.do_sleep(30)
	a = raw_input("test: ")
	advertise.announce('forwarder', 'happy', 800)
	ip = advertise.lookup('forwarder')
	ip2 = forwarder_advertise.flookup()
	
	sip = server_advertise.slookup('mac address')
	
	