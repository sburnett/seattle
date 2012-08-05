# oddball killing the parent test...2
# Kill Repy resource monitor.

import nonportable
import subprocess
import time
import os
import signal
import harshexit
import utfutil
import sys

 
def main():

  repy_args = [sys.executable, 'repy.py', 
               'restrictions.default',
               'test_killp_writetodisk.py']

  
  if nonportable.ostype == 'Darwin' or nonportable.ostype == 'Linux':

    process = subprocess.Popen(repy_args, 
                               stdout = subprocess.PIPE, 
                               stderr = subprocess.PIPE)
    pid = process.pid

    # Give it a few seconds to start.
    time.sleep(4)


    # Find the orphaned child's PID.

    # Run <ps> and print the first field (PID) of the line with second 
    # field (PPID) equal to the parent pid.
    if nonportable.ostype == 'Darwin' or nonportable.osrealtype == 'FreeBSD':
      command = "ps -aO ppid | awk '{if ($2==" + str(pid) + ") {print $1}}'"      
    elif nonportable.ostype == 'Linux':
      command = "ps -ef | awk '{if ($3==" + str(pid) + ") {print $2}}'"

    (out, error) = subprocess.Popen(command,
                                    stdout = subprocess.PIPE, 
                                    stderr = subprocess.PIPE, 
                                    shell = True).communicate()
    child_pid = out.strip()

  # Windows 
  elif nonportable.ostype == 'Windows' or nonportable.ostype == 'WindowsCE':
    # This is much easier because we don't worry about the path or have 
    # children to worry about.
    process = subprocess.Popen(repy_args,
                               stdout = subprocess.PIPE,
                               stderr = subprocess.PIPE)

    pid = process.pid
    
    # Wait while the process starts.
    time.sleep(4)

  else:
    print "Error: Unknown OS type '" + nonportable.ostype + "'!"
    sys.exit(1)



  # Kill the repy resource monitor.
  harshexit.portablekill(pid)
  time.sleep(1)
  
  # See ticket #413 and #421
  # This is a workaround for the possibility that the repy child was sleeping
  if nonportable.ostype == 'Darwin' or nonportable.ostype == 'Linux':
    # Send SIGCONT to the child if the process still exists, it should wake up,
    # get a read error when checking the pipe, and then exit...
    try: os.kill(int(child_pid), signal.SIGCONT)
    except OSError: pass # The child has likely exited
      
    # Wait for the signal to take effect
    time.sleep(1)    

  # Make sure the file size is not changing
  firstsize = os.path.getsize("junk_test.out")
  time.sleep(1)
  secondsize = os.path.getsize("junk_test.out")
  

  if firstsize != secondsize: print 'FAIL'



    
if __name__ == '__main__':
  main()
