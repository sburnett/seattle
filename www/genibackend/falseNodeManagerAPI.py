import random

userdict = {}

def init_nmapi():
  pass

def dosignedcall(ip, port, pubkey, privkey, *callargs):
  if random.random()>.8:
    raise Exception("Random error doing signed call")
  vesselname = ip +':'+ str(port) + ':'+callargs[1]
  
  if callargs[0] == 'ChangeUsers':
    if vesselname not in userdict:
      userdict[vesselname] = []
    if ((callargs[2] == '') or (userdict[vesselname] == '')):
      userdict[vesselname] = callargs[2]
    else:
      print "OH NO!!!   old: "+str(userdict[vesselname])+" new: "+str(callargs[2])
  
