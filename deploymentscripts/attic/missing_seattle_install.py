"""
<Program Name>
  missing_seattle_install.py

<Started>
  June 2009

<Author>
  n2k8000@u.washington.edu
  Konstantin Pik

<Purpose>
  This file will read in a list file passed into it, and from that list it
  will install seattle on all of those nodes.  The list file is to be in the
  file format specified for .LIST files (!user:[username], followed by list of
  IPs).

<Usage>
  python missing_seattle_install.py missing.list
  
  Note: missing.list is the default file name.
  
"""

import thread
import time
import sys

# for remote_shellexec
import deploy_network
import deploy_threading

# the running thread counter
thread_counter = 0

# the lock on the thread_counter, just to make sure add/sub is atomic
thread_lock = thread.allocate_lock()



def get_remote_hosts_from_file(fname = 'missing.list'):
  """
  <Purpose>
    Returns a list of the IP as read from file specified. 

    File format is:
  
    !user:[username]
    [IPs]

    [username] is the username that will be used until a new $username is 
      specified in the same format. NOTE: Username is case sensitive.
    [IPs] are a list of IPs/hostname (one per line) associated with that
      username

  <Arguments>
    fname:
      Optional. The filename containing the IPs of the remote machines.  File 
      must be in the same directory as this script.
    
  <Exceptions>
    Catches a thrown exception if the IP file is not found.

  <Side Effects>
    None.

  <Returns>
    Returns a list of tuples with (username, ip) on success, False on failure
  """

  # IP file must be in the same dir as this script
  try:
    file_of_ips = open(fname, 'r')
  except Exception, e:
    print 'Error: Are you missing your list of remote hosts? ('+str(e)+')'
    file_of_ips.close()
    return False
  else:
    # flag on whether we have any remote hosts (there are users, and comments
    # in the file as well
    have_one_ip = False

    # initialize dict    
    users_ip_tuple_list = []

    current_username = ''

    # Python docs suggest doing this instead of reading in whole file into mem:
    for line in file_of_ips:

      # if first chars match what we want ('!user:' is 6 chars long)
      if line[0:6].lower() == '!user:':
        # grab everything after the '!user:' string
        # -1 so we drop the \n and leading/trailing spaces
        current_username = line[6:-1].strip()
      else:
        # ignore blank lines and spaces
        if line.strip('\n '):
          # and ignore comments (lines starting with #)
          if line.strip('\n ')[0] != '#':
            # if we get here, then we have an IP so we need to  check that 
            # user is not empty.. log err if it is and complain.
            if not current_username:
              print 'Critical Error: No username specified for remote host group!'
              file_of_ips.close()
              return False

            # add (username, remote_host) pair
            users_ip_tuple_list.append((current_username, line.rstrip('\n ')))
            # set flag that we have at least one ip
            have_one_ip = True

    # return true only if we have at least ONE ip that we added to the list 
    # and not just a bunch of users
    if have_one_ip:
      # lets make the list a set, which is a cheap way of getting rid of
      # duplicates, then cast back to list.
      finalized_list = list(set(users_ip_tuple_list))
      print "Found "+str(len(finalized_list))+" unique hosts to connect to."
      file_of_ips.close()
      return finalized_list
    file_of_ips.close()
    return False

 

def format_print(out, err):
  """
  <Purpose>
    Will print out the non-empty out/err strings once they're properly
    formatted. Intended to format stdout and stderr. Also will print to 
    missing.log

  <Arguments>
    out:
      stdout
    err:
      std error

  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    None.
  """
  try:
    out = out.strip('\n\r ')
    err = err.strip('\n\r ')
    
    logfilehandle = open('missing.log', 'a')
    
    if out:
      print out
      logfilehandle.write(out+'\n')
    if err:
      print err
      logfilehandle.write(err+'\n')
      
    logfilehandle.close()
  except Exception, e:
    print 'Error while writing file and/or formatting data'
    print e
    
  return

def worker(cmd, username, host):
  """
  <Purpose>
    Worker thread that makes calls to remote_shellexec and increments
    the running thread counter until the thread has finished.

  <Arguments>
    cmd:
      the command string to execute on the machine
    username:
      the username to log in as
    host:
      the remote hostname/ip to install on.

  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    None.
  """
  
  global thread_counter, thread_lock
  # do an atomic add on the number of threads running
  thread_lock.acquire()
  thread_counter += 1
  thread_lock.release()
  
  out, err, retcode = deploy_network.remote_shellexec(cmd, username, host)
  
  format_print('|\n\n Log from node: '+host+'\n'+out, err)
  
  # do an atomic subtract on the number of threads running
  thread_lock.acquire()
  thread_counter -= 1
  thread_lock.release()

  
  
def main():
  """
  <Purpose>
    Entry point into the program.  Reads the hosts that need installing
    from file and then starts the threads that will take care of downloading
    and installing seattle.  Then waits for all threads to finish.  This takes
    a while as an RSA key needs to be generated during each install.

  <Arguments>
    None

  <Exceptions>
    Possible exception when launching new threads.

  <Side Effects>
    None.

  <Returns>
    None.
  """
  
  # start the timeout monitor thread
  deploy_threading.init()
  
  # the fn of the file that contains the list of nodes we'll be using
  nodelist_fn = ''
  
  # did we get a parameter passed in? if so that's our fn
  if len(sys.argv) > 1:
    nodelist_fn = sys.argv[1]
    print 'Using '+nodelist_fn+' filename to read in hostnames'
  else:
    print 'Using default missing.list filename to read in hostnames'
    
  # get hosts from file
  if nodelist_fn:
    hosts = get_remote_hosts_from_file(nodelist_fn)
  else: # use default fn
    hosts = get_remote_hosts_from_file()
  
  # if we have hostnames
  if hosts:
    # build up a command string that'll download and install seattle
    cmd_list = []
    
    # try to uninstall seattle_repy, then remove dir
    cmd_list.append('cd seattle_repy; ./stop_seattle.sh; ./uninstall.sh')
    # 1. Remove old file, and download the file
    cmd_list.append('cd ~; rm -rf seattle_linux.tgz; rm -rf seattle_repy')
    
    cmd_list.append('wget https://seattlegeni.cs.washington.edu/geni/download/flibble/seattle_linux.tgz')
    
    
    # 2. Untar
    cmd_list.append('tar -xf seattle_linux.tgz')
    
    # 3. Change into seattle_repy directory and execute python install.py and start seattle
    cmd_list.append('cd seattle_repy; python install.py; ./start_seattle.sh ')
    
    # merge into a command string
    cmd_str = '; '.join(cmd_list)
    
    while hosts:
      # 8 is the number of threads we'll launch
      while thread_counter < 8:
        # grab a tuple from hosts array
        host = hosts.pop()
        
        # separate it out for clarity
        user = host[0]
        machine = host[1]
        
        print 'Starting on '+str(machine)
         
        try:
          # start thread and then give it some time to boot up
          thread.start_new_thread(worker, (cmd_str, user, machine,))
          time.sleep(.2)
        except Exception, e:
          print "Exception while trying to start worker thread"
          print e
          return
      
    # wait until we're done...
    while thread_counter > 0:
      time.sleep(1)
      
      
      
if __name__ == "__main__":
  main()
