"""
<Program>
  run_parallel_node_script.py

<Purpose>
  This program is used to run a shell script on a set
  of nodes in parallel. If the script hangs on any of 
  the nodes, it is killed after a certain time period.

<Author>
  Monzur Muhammad (monzum@cs.washington.edu)
"""

import os
import sys
import time
import threading
import subprocess

from threading import Timer
from threading import Thread





def kill_ssh_process(ssh_pid, node_ip):
  """
  Kills a process given it's pid.
  """
  print "The node " + node_ip + " is hanging. Killing ssh process."
  # Kill process thats hanging
  subprocess.Popen(["kill", '-s', '9', str(ssh_pid)])


class run_script(Thread):
  """
  Runs a bash script in parallel given the ip address of a node,
  the login username and the seattleclearinghouse username.
  """

  def __init__ (self,ip, script_name, username,seattle_user):
    Thread.__init__(self)
    self.ip = ip
    self.script_name = script_name
    self.username = username
    self.seattle_user = seattle_user
  def run(self):
    command = ["/bin/bash", self.script_name, self.ip, self.username, self.seattle_user]
    process = subprocess.Popen(command)


    # If the process does not finish in 120 seconds, then we want to kill it.
    timeout_timer = Timer(120, kill_ssh_process, [process.pid, self.ip])
    timeout_timer.start()
    
    process.wait()
    timeout_timer.cancel()



def main(fd):
    
    iplist = []

    script_name = sys.argv[2]
    ssh_username = sys.argv[3]
    seattle_username = sys.argv[4]

    # Read in all the ip addresses from a file and add each tuple of 
    # the ip address and the bash script to run in a threading list
    # Then start up the thread.
    for ip in fd:
      if ip:
        current = run_script(ip, script_name, ssh_username, seattle_username)
        iplist.append(current)
        current.start()
        time.sleep(1)


          
if __name__ == "__main__":
  if len(sys.argv) < 5:
    print "Incorrect amount of arguments provided."
    print "Usage:\n\tpythnon run_parallel_node_script ip_file_path bash_script_path ssh_login_name seattle_user_name "
    print "Example:\n\tpython run_parallel_node_script ip_list.txt install_seattle.sh uw_affiliate test_seattle_user"
    sys.exit(1)

  fd = open(sys.argv[1],"r").read().split('\n')

  main(fd)

  
