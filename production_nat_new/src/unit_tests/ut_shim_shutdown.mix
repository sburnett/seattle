import os
import sys
import time
import harshexit
import runonce

if __name__ == '__main__':

  # If we are in testmode, then there should be a file stored in local directory
  # called nodemanager.pid, that stores the pid of the nodemanager that was 
  # started in test mode. If the file does not exist, then check if the lock
  # for the nodemanager was acquired.
  try:
    nmmain_pid_file = open("nodemanager.pid", 'r')
  except IOError, e:
    # Stop the NM
    gotlock = runonce.getprocesslock("seattlenodemanager")
    if gotlock == True:
      # No NM running? This is an error
      print "FAILURE: Successfully acquired the NM process lock! The NM should be running!\n"
    elif gotlock:
      # Kill the NM
      harshexit.portablekill(gotlock)
      # Allow the sockets to cleanup and the locks to be cleaned
      time.sleep(3)
      sys.exit(0)
    else:
      print "FAILURE: Was unable to shutdown the nodemanager! Please manually kill it."
    
    sys.exit(1)


  # If we were able to open the file   
  nodemanager_pid = int(nmmain_pid_file.read())
  nmmain_pid_file.close()
  harshexit.portablekill(nodemanager_pid)
  
  # Remove the pid file now that we are done with the tests.
  os.remove('nodemanager.pid')

  # Wait for everything to get cleaned up.
  time.sleep(3)
