from remote_emulab import *


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
exp = "helloworld3"

#specify the name of an ns file being used
myns = "hello.ns"


# EXECUTE A BASIC SENERIO

# read the ns file into a string
file = open(myns)
filestr = file.read()

# check the ns file for errors
(passed,message) = checkNS(filestr)


# did the parseing fail?
if (not passed):
  print message
  print "checkNS failed, please fix the ns file and try again"

else: 
  # start a new exp in non-batchmode
  print "starting a new exp..."
  startexp(proj,exp,filestr)

  # wait for the exp to go active
  # by default times out in 10 minutes
  print "exp started, waiting for active..."
  wait_for_active(proj,exp)

  print "now active... getting mapping"
  print "mapping:  "+str(get_mapping(proj,exp))
  print " got mapping, getting links"
  print "links:  "+str(get_links(proj,exp))

  # exit this code, go and do your expirament
  # when the exp is done we'll swap it out

  print "finished exp, swapping out"
  swapOUT(proj,exp)
  print "swaped out"


  # Some additional notes.  
  # Since we did a swap out and not an endexp
  # the exp will still exisit in emulab
  # we can re run it, or modify it and re run it
