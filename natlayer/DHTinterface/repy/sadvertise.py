include centralizedadvertise.repy


# both sadvertise and slookup takes a mac address as key

def sadvertise(key, waittime = 180):
	while True:
		# register current forwader under key
		centralizedadvertise_announce(key, mycontext['currforwarder'], waittime * 2)
		
		sleep(waittime)

def slookup(key, maxvals = 100):

	# given a key, e.g. mac address, finds the currforwarder of target user
	mycontext['targetforwarder'] =  centralizedadvertise_lookup(key)
	


#below is the code for starting the server advertise thread in repy
	
#if callfunc == 'initialize':
#	settimer(0, sadvertise, [mycontext['forwarderip']] )
