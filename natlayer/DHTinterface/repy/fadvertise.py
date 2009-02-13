include centralizedadvertise.repy


# forwarder advertise registers all forwarder ip addresses under the key 'forwarder' 
# does not have open DHT

def fadvertise(waittime = 300):
	while True:	
		#get current ip
		mycontext['forwarderip'] = getmyip()
		
		centralizedadvertise_announce('forwarder', mycontext['forwarderip'], 600)
		
		sleep(waittime)

def flookup(maxvals = 100):
	# get the list of forwarders
	flist = centralizedadvertise_lookup('forwarder', maxvals)
	
	# grab random forwarder
	a = int(randomfloat() * 1000)
	index = a % len(flist)
	
	# store the value
	mycontext['currforwarder'] = flist[index]

# below is code for starting the forwarder advertise thread in repy

#if callfunc == 'initialize':
#	mycontext['forwarderip'] = getmyip()
#	settimer(0, fadvertise, ('forwarder', mycontext['forwarderip']) )
