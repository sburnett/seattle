"""
<Program Name>
  deploy_server_monitor.py

<Started>
  July 2009

<Author>
  n2k8000@u.washington.edu
  Konstantin Pik

<Purpose>
  The purpose of this file is to make sure that the web server is running, as
  well as the monitoring scripts are started up every so often.

<Usage>
  python deploy_server_monitor.py
  
"""

import time
import sys
import deploy_main
import thread


def webserver_is_running():
  """
  <Purpose>
    Check to see if the webserver is running
     
  <Arguments>
    None.
    
  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    Boolean. True/False: is the webserver running?
  """
  # True if running, false if not. checks via ps
  out, err, retcode = deploy_main.shellexec2('ps -ef | grep deploy_server_final.py | grep -v grep')
  # if -1, then not running, otherwise it is
  return out.find('python deploy_server_final.py') > -1
  
  
  
def deploymentscript_is_running():
  """
  <Purpose>
    IChecks to see if the deployment scripts (deploy_main.py) are running.
     
  <Arguments>
    None.
    
  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    Boolean. True/False: are the scripts running
  """
  # True if running, false if not. checks via ps
  out, err, retcode = deploy_main.shellexec2('ps -ef | grep deploy_main.py | grep -v grep')
  # -1 if not running, otherwise it is
  return out.find('python deploy_main.py') > -1


  
def server_monitor():
  """
  <Purpose>
    This method runs on its own thread called from main().  It checks to see
    if the webserver is running, and if it is not, it'll restart the webserver.
    Thread checks to see if the webserver is running every 2 minutes.
     
  <Arguments>
    None.
    
  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    None. 
  """
  
  # check if server's running every several mins
  if not webserver_is_running():
    # not running, restart it in a non-blocking way, and fwd all stdout to webserver.log
    deploy_main.shellexec2('python deploy_server_final.py > ~/webserver.log 2>&1 < /dev/null&')
    #deploy_main.shellexec2('python deploy_server_final.py > /dev/null 2> /dev/null < /dev/null&')
    
  time.sleep(120)
  
  # let this thread die, and start a new one.
  thread.start_new_thread(server_monitor, ())


def stop_web_server():
  """
  <Purpose>
    Stops all instances of the webserver (if for some reasont there were 
    multiple instances running
     
  <Arguments>
    None.
    
  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    None. 
  """
  
  # if for some reason there are multiple processes running
  while webserver_is_running():
    deploy_main.shellexec2("ps -ef | grep deploy_server_final.py | grep -v grep | awk ' { print $2 } ' | xargs kill -9")
  
  
  
def stop_deployment_scripts():
  """
  <Purpose>
    Stops all instances of the deployment scripts (deploy_main.py) if there 
    were multiple instances launched for some reason (although this should 
    never occur unless someone was launching them manually).
     
  <Arguments>
    None.
    
  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    None. 
  """
  while deploymentscript_is_running():
    deploy_main.shellexec2("ps -ef | grep deploy_main.py | grep -v grep | awk ' { print $2 } ' | xargs kill -9")

    
def stop_ssh_scp():
  """
  <Purpose>
    Stops all possibly hung ssh/scp processes.
     
  <Arguments>
    None.
    
  <Exceptions>
    None.

  <Side Effects>
    Might close the users ssh session.

  <Returns>
    None. 
  """

  deploy_main.shellexec2("ps -ef | grep 'ssh -T' | awk '{ if ($1 == \"nsr\") print $2 } ' | xargs kill -9")
  deploy_main.shellexec2("ps -ef | grep 'ssh -x' | awk '{ if ($1 == \"nsr\") print $2 } ' | xargs kill -9")
  deploy_main.shellexec2("ps -ef | grep 'scp -o' | awk '{ if ($1 == \"nsr\") print $2 } ' | xargs kill -9")
   
   
def check_ssh_agent():
  """
  <Purpose>
    Checks to see if ssh-agent is running, if not it should start it.
     
  <Arguments>
    None.
    
  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    None. 
  """
  # checks to see if ssh-agent is running, and if not, then it'll start it
  # at this point, as the script is intended to run on nsr, the key has no passphrase
  out, err, returncode = deploy_main.shellexec2("ps -ef | grep ssh-agent | awk '{ if ($1 == \"nsr\") print $8 }'")
  if out.find('ssh-agent') > -1:
    # good, at least one instance is running
    pass
  else:
    print "ssh-agent is not running"
    # not running.. let's boot it up
    deploy_main.shellexec2("eval `ssh-agent`; ssh-add ")
  
  
  
def script_monitor():
  """
  <Purpose>
    This method runs on its own thread.  It checks to see if the scripts 
    are done and once they are, it'll launch them again roughly every 90 mins.
    If the script are not done after 90 mins, the thread will sleep for 5 mins
    at a time for a recheck.
     
  <Arguments>
    None.
    
  <Exceptions>
    None.

  <Side Effects>
    See stop_ssh_scp().

  <Returns>
    None. 
  """
  
  # if the timeout is up, make sure that the last round of tests has finished
  while deploymentscript_is_running():
    # while it's still running, sleep 5 mins at a time until it's not done
    time.sleep(60 * 5)
  
  # kill all old, possibly hung ssh-processes
  # bug?: this'll close anyone's ssh-session who's connected as 
  # nsr@blackbox when scripts connect.
  stop_ssh_scp()
  #check_ssh_agent()
  # run in non-blocking way.
  deploy_main.shellexec2('python deploy_main.py -c custom.py > /dev/null 2> /dev/null < /dev/null&')
  # sleep for 1.5 hrs. if scrips aren't done yet, it'll stall 5 mins at a time
  time.sleep(60 * 90)
  
  thread.start_new_thread(script_monitor, ())


def is_monitor_already_running():
  """
  <Purpose>
    Checks to see whether another monitor process (deploy_server_monitor.py) is already
    running.
     
  <Arguments>
    None.
    
  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    Boolean. True/False: is more than one monitor running?
  """
  
  # check to see whether another instance of this script is already running
  out, err, retcode = deploy_main.shellexec2("ps -ef | grep deploy_server_monitor | grep -v grep "+\
    "| awk '{ if ($1 == \"nsr\") print $1 } ' | sort | uniq -c | awk ' { print $1 } '")
  if out:
    try:
      num_running = int(out)
      if num_running == 1:
        return False
      else:
        return True
    except Exception, e:
      # something went wrong..
      print 'Error in is_monitor_already_running'
      return True
  else:
    return False
      

def main():
  """
  <Purpose>
    Entry point. Launches the two monitoring threads:
      - the http server monitor
      - the deployment scripts monitor
     
  <Arguments>
    If sys.argv[1] has an argument and that argument is 'kill', then we
    need to stop everything and kill everything.
    
  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    None. 
  """

  # if we have an arg passed to us, then we need to kill the server
  if len(sys.argv) == 2:
    # is it kill?
    if sys.argv[1] == 'kill':
      # stop the web server
      stop_web_server()
      # sto the deployment scripts
      stop_deployment_scripts()
      # cleanup any hung ssh/scp possibly left over from the deployment scripts
      stop_ssh_scp()
      print "Everything stopped successfully"
  else:
    # just need to launch the server, so if we're not already running
    # then we'll launch the scripts, otherwise just clean exit.
    if not is_monitor_already_running():  
      thread.start_new_thread(server_monitor, ())
      thread.start_new_thread(script_monitor, ())
      
      while True:
        # so we don't spam, we just need to spin this main thread and keep it 
        # from exiting
        time.sleep(60)
    else:
      print "Monitor is already running."
  
  
  
if __name__ == "__main__":
  main()
