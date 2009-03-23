include centralizedadvertise.repy

"""

Author: Dennis Ding

Start date: January 22, 2009

Description: Provides the implentation to register and lookup the IP address of potential forwarders

"""


# forwarder advertise registers all forwarder ip addresses under the key 'forwarder' 
# does not have open DHT
    
def forwarder_advertise(waittime = 300):
  myip = getmyip()

  while True:	
    #try:
    centralizedadvertise_announce('forwarder', myip, 600)
    #except:
    sleep(waittime)


def forwarder_lookup(maxvals = 100):
  # get the list of forwarders
  flist = centralizedadvertise_lookup('forwarder', maxvals)
	
  # grab random forwarder
  index = int(randomfloat() * len(flist))
	
	
  # store the value
  mycontext['currforwarder'] = flist[index]
  return (mycontext['currforwarder'], 12345)

# below is code for starting the forwarder advertise thread in repy

#if callfunc == 'initialize':
#	mycontext['forwarderip'] = getmyip()
#	settimer(0, fadvertise, [] )
