import runonce
import time
import os

lockname = "seattletestlock"

print "my process id is:"+str(os.getpid())
retval = runonce.getprocesslock(lockname)
if retval == True:
  print "I have the mutex"
elif retval == False:
  print "Another process has the mutex (owned by another user most likely)"
else:
  print "Process "+str(retval)+" has the mutex!"

while True:
  time.sleep(2)
  if runonce.stillhaveprocesslock(lockname):
    print "I have the mutex"
  else:
    print "I do not have the mutex"
