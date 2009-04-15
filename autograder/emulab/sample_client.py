#from remote_emulab import *
import remote_emulab

# This is a very rough sample of what a client
# to the remote_emulab.py library will look like
#
# Everything below is hardcoded and is not intended
# to be executed (it will fail because it assumes a
# new and unique exp name).  It is just an exmaple 
# senerio. 

# if you want to run it and see it work, first you'll
# need to set up keys and your login for remote_emulab.py
# then just change exp below from "helloworld"+n to
# "helloworld"+(n+1) so that the name will be unique.
# You should probably be polite and permanately remove the
# the new exp from emulab when you are done.


# SETUP SOME CONSTANTS

# specify the emulab proj name, this is always 'Seattle'
proj = "Seattle"

# specify the exp name, this is unique for any class assignment
exp = "lantest"

#specify the name of an ns file being used
mynsfn = "hello.ns"


# EXECUTE A BASIC SENERIO

# read the ns file into a string
mynsfobj = open(mynsfn)
mynsfilestr = mynsfobj.read()
mynsfobj.close()

# check the ns file for errors
(passed,message) = remote_emulab.checkNS(mynsfilestr)




# did the parsing fail?
if (not passed):
  print message
  print "checkNS failed, please fix the ns file and try again"

else: 
  # start a new exp in non-batchmode
  print "starting a new exp..."
  remote_emulab.startexp(proj,exp,mynsfilestr)

  # wait for the exp to go active
  # by default times out in 10 minutes
  print "exp started, waiting for active..."
  remote_emulab.wait_for_active(proj,exp)

  print "now active... getting mapping"
  mapping = remote_emulab.get_mapping(proj,exp)
  print "mapping:  "+str(mapping)
  simple_mapping = get_ips(mapping)
  

  print " got mapping, getting links"
  print "links:  "+str(remote_emulab.get_links(proj,exp))

  # exit this code, go and do your expirament
  # when the exp is done we'll swap it out

  print "finished exp, swapping out"
  #remote_emulab.swapOUT(proj,exp)
  print "swaped out"


  # Some additional notes.  
  # Since we did a swap out and not an endexp
  # the exp will still exisit in emulab
  # we can re run it, or modify it and re run it
