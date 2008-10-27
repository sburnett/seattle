import runonce
import os
import sys
import nonportable

locklist = [ "seattlenodemanager", "softwareupdater.old", "softwareupdater.new" ]

def main():

  # For each locked process, find the PID of the process holding the lock...
  for lockname in locklist:
    retval = runonce.getprocesslock(lockname)
    if retval == True:
      # I got the lock, it wasn't running...
      print "The lock '"+lockname+"' was not held"
      pass
    elif retval == False:
      # Someone has the lock, but I can't do anything...
      print "The lock '"+lockname+"' is not held by an unknown process"

    else:
      # I know the process ID!   Let's stop the process...
      print "Stopping the process (pid: "+str(retval)+") with lock '"+lockname+"'"
      nonportable.portablekill(retval)


if __name__ == '__main__':
  main()
