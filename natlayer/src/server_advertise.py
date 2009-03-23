include centralizedadvertise.repy


# both sadvertise and slookup takes a mac address as key

def server_advertise(key, waittime = 180):
  while True:
    # register current forwader under key
    centralizedadvertise_announce(key, mycontext['currforwarder'], waittime * 2)

    sleep(waittime)

def server_lookup(key, maxvals = 100):

  # given a key, e.g. mac address, finds the currforwarder of target user
  mycontext['targetforwarder'] =  centralizedadvertise_lookup(key)

  return (mycontext['currforwarder'], 12345)


#below is the code for starting the server advertise thread in repy
	
#if callfunc == 'initialize':
#	settimer(0, sadvertise, [mycontext['forwarderip']] )
