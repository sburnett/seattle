"""
<Program Name>
  deploy_threading.py

<Started>
  May 2009

<Author>
  n2k8000@u.washington.edu
  Konstantin Pik

<Purpose>
  This is the file contains threading-related functions that are used by the 
  deployment script.  This file is not to be executed by itself, but is to
  be used with the deploy_* modules.

<Usage>
  See deploy_main.py.
  
"""

import deploy_logging
import deploy_helper
import parallelize_repy
import thread
import time
import os


# the number of threads to launch max
threadsmax = 25

# Thread communication dictionary. Used for communication between threads
thread_communications = {}

# lock for the dictionary
thread_communications_lock = thread.allocate_lock()

# Set that the module hasn't been initialized yet
thread_communications['init'] = False


   
def start_thread(callfunc, arguments, max_threads):
  """
  <Purpose>
    Starts the worker threads and calls init() for this module.  This'll allow for 
    the timeout thread to function properly.
    
    intended to be called only from connect_and_do_work.
    
  <Arguments>
    callfunc:
      the function to call.
    arguments:
      the list of tuples where each tuple is (username, host) to connect to
    max_threads:
      the max # of threads to start.
    
  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    Boolean.
    
    True on success.
    False on failure.
  """
  init()
  func_handle = parallelize_repy.parallelize_initfunction(arguments, callfunc, max_threads) 
  thread_communications['func_handle'] = func_handle
  thread_communications['hosts_left'] = arguments[:]
  thread_communications['total_hosts'] = len(arguments)



def has_unreachable_hosts():
  """
  <Purpose>
    Checks to see if we have any hosts sitting in our list that contains
    the unreachable hosts.
    
  <Arguments>
    None.    
    
  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    Boolean.
    
    True on success.
    False on failure.
  """
  # if there is at least one entry in the list, then we have at least
  # one host that was unreachable.
  return len(thread_communications['unreachable_host']) > 0


def destroy():
  """
  <Purpose>
    Resets this module to it's initial state, opposite of init().
    
  <Arguments>
    None.    
    
  <Exceptions>
    On any type of exception it'll return false.

  <Side Effects>
    None.

  <Returns>
    Boolean.
    
    True on success.
    False on failure.
  """
  try:
    # initialize, keep track of how many threads are running
    thread_communications['threads_running'] = 0

    # set the kill flag to false and start the thread monitoring pids
    thread_communications['kill_flag'] = True
    
    # tells the module it has been initialized
    thread_communications['init'] = False
  except Exception, e:
    print e
    return False
  else:
    return True


def init():
  """
  <Purpose>
    Initializes all the globals and things to the default values and
    starts the thread that deals with killing processes started that
    have timed out.
    
  <Arguments>
    None.    
    
  <Exceptions>
    Critical exception thrown if thread monitor could not be started.

  <Side Effects>
    None.

  <Returns>
    Boolean.
    
    True on success.
    False on failure.
  """

  # initialize, keep track of how many threads are running
  thread_communications['threads_running'] = 0

  # set the kill flag to false and start the thread monitoring pids
  thread_communications['kill_flag'] = False
  
  # tells the module it has been initialized
  thread_communications['init'] = True
  
  try:
    thread.start_new_thread(pid_timeout, ())
  except Exception, e:
    deploy_logging.logerror("Trouble starting pid thread monitor")
    return False
    # clone my hosts: this entry in the dict will keep track of what elements' 

  return True



def node_was_reachable(node):
  """
  <Purpose>
    Checks to see if the node was reachable, or if it's in the unreachable 
    pile.

  <Arguments>
    node:
      A list with a single element which is a tuple containing 
      (username, hostname).

  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    Boolean.
    
    True on node was reachable.
    False on node was unreachable.
  """  
  # if the node is in not found inside the unreachable_hosts set, then it was
  # obviously reachable
  return node not in set(thread_communications['unreachable_host'])



def add_instructional_node(node):
  """
  <Purpose>
    Adds an instructional machine to the list of instructional machines. 
    Creates the array if necessary.

  <Arguments>
    Node:
      A list with a single element which is a tuple containing 
      (username, hostname).

  <Exceptions>
    None.

  <Side Effects>
    Modifies a list in the global dictionary

  <Returns>
    None.
  """  
  
  # adds a node to the instructional machine nodelist
  if 'instructional_machines' in thread_communications.keys():
  # it exists, just add
    thread_communications['instructional_machines'].append(node)
  else:
    # doesn't exist, create array, then add
    thread_communications['instructional_machines'] = [node]


def subtract_host_left(hosts, sub_counter = True):
  """
  <Purpose>
    Subtracts the finished host from the list of hosts that are still running.

  <Arguments>
    hosts:
      List of tuple of form (username, hostname) that have finished.
    sub_counter:
      Tells us to subtract the running threads counter.

  <Exceptions>
    None.

  <Side Effects>
    Modifies a list in the global dictionary

  <Returns>
    None.
  """  
  
  # subtract us from the running hosts
  # basically convert host (which is a tuple of (username, hostname)) to a set
  # and then convert hosts_left entry in the list to a set as well and then
  # perform set subtraction and cast back to a list.
  threading_lock()
  thread_communications['hosts_left'] =\
      list(set(thread_communications['hosts_left']) - set(hosts))
  threading_unlock()
  if sub_counter:
    threading_lock_and_sub()



def add_unreachable_host(host_tuple):
  """
  <Purpose>
    Adds host (which is a (username, host) tuple) to the list of failed # 
    of hosts in the dictionary

  <Arguments>
    None.

  <Exceptions>
    None.

  <Side Effects>
    Modifies a list in the global dictionary

  <Returns>
    None.
  """

  thread_communications['unreachable_host'].append(host_tuple)



def threading_currentlyrunning():
  """
  <Purpose>
    Helper method for figuring out if the function is still running or not.

  <Arguments>
    None.

  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    Boolean. Is the function done or not?
  """
  
  # grab the function handle and then the results of that function
  func_handle = thread_communications['func_handle']
  
  threads_running = parallelize_repy.parallelize_isfunctionfinished(func_handle)
  results_dict = parallelize_repy.parallelize_getresults(func_handle)
  size = thread_communications['total_hosts']
  print str(len(results_dict['aborted']))+' aborted, '+str(len(results_dict['exception']))+\
      ' exceptioned, '+str(len(results_dict['returned']))+' finished of '+str(size)+' total.'

  return not threads_running



def threading_lock():
  """
  <Purpose>
    Helper method for getting for locking the thread dictionary

  <Arguments>
    None.

  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    None.
  """

  thread_communications_lock.acquire()
  return



def threading_unlock():
  """
  <Purpose>
    Helper method for getting for unlocking the thread dictionary

  <Arguments>
    None.

  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    None.
  """
  global thread_communications_lock
  thread_communications_lock.release()
  return



def threading_lock_and_add():
  """
  <Purpose>
    Helper method for getting for changing the number of running threads by
      incrementing our counter by 1. Takes care of locking the dictionary and
      unlocking it.

  <Arguments>
    None.

  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    None.
  """
  global thread_communications
  threading_lock()
  current_number = thread_communications['threads_running']
  thread_communications['threads_running'] = current_number + 1
  threading_unlock()
  return



def threading_lock_and_sub():
  """
  <Purpose>
    Helper method for getting for changing the number of running threads by
      decrementing our counter by 1. Takes care of locking the dictionary and
      unlocking it.

  <Arguments>
    None.

  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    None.
  """
  global thread_communications
  threading_lock()
  current_number = thread_communications['threads_running']
  thread_communications['threads_running'] = current_number - 1
  threading_unlock()
  return

  
  
def remove_host_from_hosts_left(user, remote_host):
  """
  <Purpose>
    This function is a helper which removes the host from the hosts_left
    array which keeps track of the hosts which are left to process.


  <Arguments>
    remote_host:
      the remote host to remove

  <Exceptions>
    ValueError: occurs when the host to be removed is not in the array

  <Side Effects>
    None.

  <Returns>
    None.
  """
  try:
    thread_communications['hosts_left'].remove((user, remote_host))
  except ValueError, e:
    # host is already removed, keep going
    pass
  except Exception, e:
    print e
    deploy_logging.logerror("Error in remove_host_from_hosts_left: "+str(e))
  else:
    # no error, decrease the running thread count
    threading_lock_and_sub()

  
def pid_timeout():
  """
  <Purpose>
    This function is intented to be called once and supposed to run on a 
    separate thread. Until the 'kill' flag is set, it will spin and see
    which pid's need to be killed.
    
    All process IDs are set via the set_pid_timeout method.

  <Arguments>
    None.

  <Exceptions>
    OSError: the process no longer exists, ignore
    ValueError: when removing host from running hosts this means that the
      host has already been terminated.
    Any other exception is unexpected

  <Side Effects>
    None.

  <Returns>
    None.
  """
  # keeps spinning and sleeping, checking which PIDs need to be killed
  thread_communications['running_process_ids'] = []
  # while the kill flag is false. Kill flag is modified right before
  # exit
  while not thread_communications['kill_flag']:
    # sleep and wakeup every couple seconds.
    time.sleep(5)
    # this list will keep track of the pids that we've killed
    killed_pids = []
    
    # check the running_process_ids and see if any of them have expired
    for each_process in thread_communications['running_process_ids']:
      # each process is a tuple that consists of (pid, expiretime, hostname, username)
      process_to_kill = each_process[0]
      expire_time = each_process[1]
      remote_host = each_process[2]
      user = each_process[3]
      # if the current time is past the set expire time then we need to try and kill it
      if expire_time <= time.time():
        # try to kill process
        try:
          # check if process is still running
          if os.path.exists('/proc/'+str(process_to_kill)):
            os.kill(process_to_kill, 9)
            killed_pids.append(each_process)
            # sleep a second, and then check that the process was killed. if 
            # not, try a 2nd and third time
            time.sleep(1)
            if os.path.exists('/proc/'+str(process_to_kill)):
              # try os.kill again, and if that doesn't work, use shellexec method
              os.kill(process_to_kill, 9)
              time.sleep(1)
              if os.path.exists('/proc/'+str(process_to_kill)):
                deploy_helper.shellexec2('kill -9 '+str(process_to_kill))
                time.sleep(1)
            if remote_host:
              deploy_logging.logerror("Forced kill of PID "+str(process_to_kill)+" due to timeout! The host"+\
                      " on this thread is "+remote_host)
            else:
              deploy_logging.logerror("Forced kill of PID "+str(process_to_kill)+" due to timeout!")
            # subtract from out running thread count and remove host
            subtract_host_left([(user, remote_host)])
          else:
            # the process is dead, just remove host from hosts_left just in case, and
            # remove from running pids as well, but dont sub the # of threads
            killed_pids.append(each_process)
            subtract_host_left([(user, remote_host)], False)
            
        except OSError, ose:
          # this means no pid found and process has most likely 
          # already terminated
          deploy_logging.logerror("Process"+str(process_to_kill)+"("+remote_host+") is already done.")
          subtract_host_left([(user, remote_host)], False)
          pass
        except Exception, e:
          deploy_logging.logerror("Unexpected error in pid_timeout thread "+\
            "while killing a child process: "+str(e))
    if killed_pids:
      # remove the killed pids from the list
      threading_lock()
      thread_communications['running_process_ids'] =\
          list(set(thread_communications['running_process_ids']) - set(killed_pids))
      threading_unlock()
        
def monitor_timeout(pid, sleep_time, remote_host, user):
  # launches a new thread and allows the parent thread to be not block
  # basically this covers up set_pid_timeout but launches on a different
  # thread

  thread.start_new_thread(set_pid_timeout, (pid, 2 * int(sleep_time), 
      remote_host, user))
  return
              

def set_pid_timeout(process_to_kill, sleep_time, remote_host, user):
  """
  <Purpose>
    This function sets a timeout adds it to a list that's monitored on a 
    separate thread that checks to see when the process is supposed to
    timeout.

  <Arguments>
    process_to_kill:
      the process ID to kill
    sleep_time:
      sleep time in seconds
    remote_host:
      The remote host that is on the other 'side' of this connection
      (as all process are ssh/scp)
    user:
      the username to log in as

  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    None.
  """
  
  # add this pid to the list of running PIDs. Sometimes the program exits and forgets
  # about this thread and so it keep running, we don't want that. By adding it to this
  # list, we ensure that it'll get killed from the thread-monitor thread.
  threading_lock()
  tuple_to_add = (process_to_kill, time.time()+sleep_time, remote_host, user)
  thread_communications['running_process_ids'].append(tuple_to_add)
  threading_unlock()
