#tests the fadvertise and sadvertise functions with 'macad' and current ip address

if callfunc == 'initialize':

	settimer(0, fadvertise, [] )
	flookup()
	
	targetuser = "macad"
	
	settimer(10, sadvertise, [targetuser], )
	slookup(targetuser)
	
	print mycontext['currforwarder']
	
	print mycontext['targetforwarder']
