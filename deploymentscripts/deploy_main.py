#!/usr/bin/python
"""
<Program Name>
  deploy_main.py

<Started>
  May 2009

<Author>
  n2k8000@u.washington.edu
  Konstantin Pik

<Purpose>
  Deploy test scripts on remote machines and then wait to collect output.

  Detailed:

  This script creates a .tar with several files in it, reads in a list of
  remote hosts from a file, and then uploads the .tar file to the remote 
  computers where files are extracted and executed and then the resulting
  log files are downloaded to this computer under the deploy.log/ dir. In
  That directory will be a list of folders - one for each IP, and the log
  files created by that computer run.
  
  A local log file, controller.log is created which logs the execution 
  progress of scripts.  A summary.log file is created with the summaries
  of the output (basically all the necessary information).
  
  The active working directory for the latest logs is always deploy_logs
  and older directories are renamed and gzipped with some numeral expression
  
  Arguments may be specified in any order.

<Usage>

  NOTE: -i is for compatability, and is technically not needed.
  
  python deploy.py [-v 0|1|2] [ --nokeep ] [ -h | --help ] [-c customscript1 customscript2]
        [-i instructional_list] [--cleanonly]


  -v 0
      Very silent running mode. With many hosts, it may look like the script is
       frozen so this is not recommended.
  -v 1
      Default verbosity level. Same as -v 3 but makes more compact log files by
        filtering out excess information.
  -v 2
      Specifies if a more verbose mode is to be used. When verbose 
        mode is flagged, then the local log file (controller.log) will contain
        a bunch of data (such as most of the stdout from the remote host).
        This is not recommended to be set if you are connecting to a lot 
        of machines. On the other hand, it presents everything in one file
        neatly.
  --nokeep
      If --nokeep is specified, the old log files will be deleted and not
        moved (and appended with a .number). Note that the default action
        is to keep all old log files
  -h, --help
      Shows usage info with all flags.
  -c fn1 fn2 ...
      Must be followed by a valid python script file.  This file will be packaged
        and distributed to all the computers.  NOTE: As of this version, only ONE
        script will execute remotely.
  -i instructional_list
      Must be followed by a valid IP list file. The hostnames/ips in this file
        will be treated slightly different (lower threadcount to avoid connection
        refused message).
  -l list
      Custom list of IPs to use.

      
  TODO:
  --cleanonly
      If specified the remote computers will only be cleaned (all files created
        by this script will be removed).

  IMPORTANT: One file that is not created by this script (BUT IS IMPORTANT) is the
    dictionary file of hashes created by verifyfiles.py. As of this release, I have
    provided a sample version (version h).
"""



import os
import subprocess
import time
import thread
import sys
import getopt

# import of local deploy_* libraries
import deploy_logging
import deploy_network
import deploy_threading

# Verbose Flag - specifies whether we dump a bunch of stuff to the local log
# directory or not. -v means false, -vv means true.
verbosity = 1

# custom list
custom_list_file = ''

# default number of tries to retry a connection if it was refused
number_of_default_retries = 3

# The file that we read our hostlist from.
custom_host_file = 'iplist2.list'

# The variable that'll keep track of the custom scripts we'll be using
custom_script_name = ''



def print_notification():
  """
  <Purpose>
    Internal helper method. Just prints a notification.
     
  <Arguments>
    None.
    
  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    None. 
  """
  print deploy_logging.sep
  print 'This script will create an updated tar of the necessary files, and then'
  print 'it will execute a script that uploads the tar to the remote computers.'
  print 'After that it will attempt to run the scripts remotely, and log all '
  print 'produced output'
  print deploy_logging.sep

  
  
def shellexec2(cmd_str):
  """
  <Purpose>
    Uses subprocess to execute the command string in the shell.
     
  <Arguments>
    cmd_str:  The string to be treated as a command (or set of commands,
                deploy_logging.separated by ;).
    
  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    A tuple containing (stdout, strerr, returncode)

    Detailed:
    stdout: stdout printed to console during command execution.
    strerr: error (note: some programs print to strerr instead of stdout)
    returncode: the return code of our call. If there are multiple commands, 
                then this is the return code of the last command executed.
  """

  # get a handle to the subprocess we're creating..
  handle = subprocess.Popen(cmd_str, shell=True, 
      stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

  # execute and grab the stdout and err
  stdoutdata, strerrdata = handle.communicate("")

  # The return code...  
  returncode = handle.returncode
  
  return stdoutdata, strerrdata, returncode

  
  
def prep_local_dirs(keep):
  """
  <Purpose>
    Just prepares local directories - cleans the old log folders if needed
      or moves them around, and creates a temp folder that'll be used later
     
  <Arguments>
    keep: Boolean. Do we keep the old log directory?
    
  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    None.
  """
  # delete the directory if it exists
  if not keep:
    if os.path.isdir("./deploy.logs/"):
      shellexec2('rm -rf ./deploy.logs/')
  else:
    # move old log dir if one exists
    if os.path.isdir("./deploy.logs/"):
      
      # find an 'integer'-suffixed directory that hasn't been taken yet
      dirindex = 1
      
      print 'Trying to move old log directory...'
      while os.path.isdir("./deploy.logs."+str(dirindex)+"/") or os.path.isfile('deploy.logs.'+str(dirindex)+'.tgz'):
        time.sleep(.2)
        dirindex += 1
      # got a folder index that doesn't exist
      shellexec2('mv ./deploy.logs/ ./deploy.logs.'+str(dirindex))
      print 'Moved old log directory successfully to ./deploy.logs.'+str(dirindex)
      print 'Tarring the directory...'
      shellexec2('tar -czf deploy.logs.'+str(dirindex)+'.tgz deploy.logs.'+str(dirindex))
      print 'Tar created, removing uncompressed files...'
      shellexec2('rm -rf deploy.logs.'+str(dirindex))
      
  # set up logs directory if one doesn't exist
  if not os.path.isdir("./deploy.logs/"):
    os.mkdir("./deploy.logs/")
    deploy_logging.log('Info', "Setting up logs directory..")
  else:
    deploy_logging.log('Info', "Logs directory found..")
    deploy_logging.log('', deploy_logging.sep)
    
  if not os.path.isdir('./deploy.logs/temp'):
    os.mkdir('./deploy.logs/temp/')
    
  return

  
  
def get_custom_script_name():
  """
  <Purpose>
    for use by other modules, will return the value of the custom_script_name
    therefore making it available. deploy_network.py uses this to figure out
    which custom script to run.
     
  <Arguments>
    None.
    
  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    A string denoting the file name of the custom script.
  """
  global custom_script_name
  return custom_script_name
  
  
  
def print_usage():
  """
  <Purpose>
    Prints the usage information for this script.
     
  <Arguments>
    None.
    
  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    None.
  """
  print "\nUsage: \ndeploy.py [-v 0|1|2] [--nokeep]"+\
          " [-h | --help] \n\t[-c customscript1 customscriptN]"+\
          "\n\t [-i instructional_list] [-l iplist2.list] \n" # TODO
  return

  
  
def main():
  """
  <Purpose>
    Entry point into the program. Called when program starts up. Sets all the
      parameters, and checks that they're all valid if set.
     
  <Arguments>
    None.
    
  <Exceptions>
    Errors are raised when something goes wrong with getops and some invalid
    args are specifies.

  <Side Effects>
    None.

  <Returns>
    Integer. 1 on error. Nothing on clean exit.
  """
  global custom_script_name
  global run_custom_script_only
  # set the flag by default to keep the old log files.
  keep = True
  
  try:
    valid_params = 'nokeep cleanonly help cleanonly customonly'.split()
    optlist, list = getopt.getopt(sys.argv[1:], ':hl:v:c:i:', valid_params)
  except getopt.GetoptError, e:
    print_usage()
    print e
    return 1
  except Exception, e:
    print_usage()
    print e
    print "Unexpected Error"
    return 1

  for opt in optlist:

    if opt[0] == '--customonly':
      # run custom files only
      run_custom_script_only = True
      
    if opt[0] == '--cleanonly':
      #cleanonly()
      pass
      
    # custom list file to use
    if opt[0] == '-l':
      # TODO: check that it's a valid file
      custom_host_file = str(opt[1])

    # show help menu
    if opt[0] == '-h' or opt[0] == '--help':
      print_usage()
      return

    # set verbosity
    if opt[0] == '-v':
      # make sure we have a verbosity specified
      if opt[1]:
        int_val = int(opt[1])
        if int_val >= 0 or int_val <= 2:
          verbosity = int(opt[1])
        else:
          verbosity = 1 # default verbosity
      else:
        print "Warning: Invalid verbosity, defaulting to 1"

    # custom file(s) to deploy
    if opt[0] == '-c':
      # not multiple and not one script specified..
      if not len(list) and not len(opt[1]):
        print "Error: No custom scripts specified. Remove -c flag please"
        return
      print "Loading custom script"

      if list:
        for custom_script in list:
          # check that the file exists
          if os.path.isfile(custom_script):
            print '\tAdding '+custom_script
            custom_script_name += custom_script+'  '
          else:
            print 'Error: '+custom_script+', a custom script is not found'
            return
      else: # just one script file
      
        # is the file we were given a real file?
        if os.path.isfile(opt[1]):
          print '\tAdding '+opt[1]
          custom_script_name = opt[1]
        else:
          print 'Error: '+custom_script_name+', a custom script is not found'
          return  
    
    # don't save old log files
    if opt[0] == '--nokeep':
      print "Erasing old log files"
      keep = False

    # instructional machines list
    if opt[0] == '-i':
      print 'Reading in instructional machine file...'
      if opt[1]:
        # check that the file exists
        if os.path.isfile(opt[1]):
          hostname_path = opt[1]
          # good now read in the file and add it to the global that 
          # keeps track of our instructional machines
          
          deploy_threading.thread_communications['machine_list'] =\
              get_remote_hosts_from_file(hostname_path)
        else:
          print "ERROR: Specified instructional machine filepath is"+\
            " not a valid file ("+opt[1]+")"
          return
      else:
        print 'Invalid instructional machine path specified, not going to die.'
        return

  # print intro
  print_notification()

  # Execute the tar creation script
  out, err, returncode = shellexec2('python create_tar.py '+custom_script_name)

  # Just formatting the out and err from executing the shell script.
  out, err = deploy_logging.format_stdout_and_err(out, err)

  # print if not empty
  if out:
    print out
  if err:
    print err
  print deploy_logging.sep

  # if all went sucessfully..
  if returncode == 0:
    # setup all the directories..
    prep_local_dirs(keep)
    
    print "Entering upload and execution script... (this may take a while)"

    # call the deploy script that'll pick up from here..
    deploy()
    print deploy_logging.sep

    # cleanup the local temp directory
    shellexec2('rm -rf ./deploy.logs/temp/')


    print 'Compacting...'
    # summarize the logfile before building the summary
    shellexec2('python log_maintenance.py dummyarg')
    
    print 'Building summary logfile..'    
    deploy_logging.build_summary()
    print deploy_logging.sep
    deploy_logging.log('Finished', 'All finished.')

  # returns 1 if there was an error.
  elif returncode == 1:
    print 'Error in creating tar.. Aborting'
  else: # just so we catch all the conditions..
    print 'CRITICAL ERROR! script returned with unexpected retcode ('+\
      str(returncode)+')'
  

  
def upload_tar(user, remote_host, tar_filename = "deploy.tar"):
  """
  <Purpose>
    This function will upload the tar to the remote_host via scp by logging 
    in as user@remote_host, and log the return code as well as anything
    printed to stderr or stdout (which is expected to be empty).
    
    Uses remote_upload_file to upload the actual file.
     
  <Arguments>
    user:
      the user to log in as on the remote machine.
    remote_host:
      the remote machine's IP to which we'll be uploading files.
    tar_filename: 
      Optional. Default is deploy.tar. The tar file to upload to the remote 
        host.
    
  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    A tuple: (returncode, stdout, stderr)
  """

  # call helper to scp  
  stdoutdata, stderrdata, returncode = deploy_network.remote_upload_file(tar_filename, user, remote_host)

  # check the return code..
  if returncode == 0:
    deploy_logging.log(remote_host, 'Successfully uploaded deploy.tar')
  else:
    deploy_logging.logerror(remote_host+': Trouble uploading deploy.tar')
  
  return (str(returncode), stdoutdata, stderrdata)

  
  
def get_current_time():
  """
  <Purpose>
    Uses python's time lib to return the current time. This is formatted
    in what I find a convenient way to show time in the logs.
     
  <Arguments>
    None.
    
  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    The date as a string. 
    
    Sample date returned: May 16 2009 00:21:51 
  """
  return time.strftime("%b %d %Y %T")

  
  
def get_remote_hosts_from_file(fname = custom_host_file, nolog = False):
  """
  <Purpose>
    Returns a list of the IP as read from file specified. 

    File format is:
  
    !user:[username]
    [IPs]

    [username] is the username that will be used until a new $username is specified
      in the same format. NOTE: Username is case sensitive.
    [IPs] are a list of IPs/hostname (one per line) associated with that username

  <Arguments>
    fname:
      Optional. Default is 'iplist.list'. The filename containing the IPs of
        the remote machines.  File must be in the same directory as this 
        script.
    nolog:
      Optional. Default is False. If set to true, then nothing will be written to the logfile.
    
  <Exceptions>
    Catches a thrown exception if the IP file is not found.

  <Side Effects>
    None.

  <Returns>
    Returns a list of tuples with (username, ip) on success, False on failure
  """

  global custom_host_file
  fname = custom_host_file
  
  # IP file must be in the same dir as this script
  try:
    file_of_ips = open(fname, 'r')
  except Exception, e:
    deploy_logging.log('Error', 'Are you missing your list of remote hosts? ('+str(e)+')')
    try:
      file_of_ips.close()
    except Exception, e:
      # not sure if we really opened it 
      pass
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
              deploy_logging.logerror('Critical Error: No username specified for remote host group!')
              file_of_ips.close()
              return False

            # add (username, remote_host) pair while casting remote_host to lowercase in case
            # it's a hostname for easy comparison if needed everywhere
            users_ip_tuple_list.append((current_username, line.rstrip('\n ').lower()))
            # set flag that we have at least one ip
            have_one_ip = True

    # return true only if we have at least ONE ip that we added to the list 
    # and not just a bunch of users
    if have_one_ip:
      # lets make the list a set, which is a cheap way of getting rid of
      # duplicates, then cast back to list.
      finalized_list = list(set(users_ip_tuple_list))
      if not nolog:
        deploy_logging.log('Setup', "Found "+str(len(finalized_list))+" unique hosts to connect to.")
      file_of_ips.close()
      return finalized_list
    file_of_ips.close()
    return False



def deploy():
  """
  <Purpose>
    This function is the brains behind the deploy script. All the main calls
    originate from this function.

    -Gets list of remote hosts from a file
    -Calls function to execute cleanup/setup on remote hosts before
      we can run remote scripts and then that same function executes
      the remote script files

  <Arguments>
    None.

  <Exceptions>
    Exit if hostlist file was not found.

  <Side Effects>
    None.

  <Returns>
    None.
  """

  # Get list of hosts
  myhosts = get_remote_hosts_from_file()

  if not myhosts: # if we didn't find any hosts.. crap out!
    print "Didn't find any remote hosts file!"
    deploy_logging.logerror("Didn't find any remote hosts file!")
    # return if we don't have instructional machines to process
    if 'machine_list' not in deploy_threading.thread_communications.keys():
      return
  else:
    # check if we also have intructional machines, and if we do, then
    # make sure we're not being tricked - remove all instructional machines
    # from the myhosts list
    if 'machine_list' in deploy_threading.thread_communications.keys():
      # we have instructional machines
      machine_list = deploy_threading.thread_communications['machine_list']
      myhosts = list(set(myhosts)-set(machine_list))
  
  # initialize thread_communications dictionary to a list which will have
  # our unreachable hosts
  deploy_threading.thread_communications['unreachable_host'] = []

  # this will keep track of the proc id's that are launched on different
  # threads. These are ssh/scp processes. We keep track of these because
  # we want to make sure that when we exit deploy.py, we kill all of these
  # processes - they should be killed by that time unless there was some kind 
  # of error.
  deploy_threading.thread_communications['running_process_ids'] = []
  
  # initial run
  connect_and_do_work(myhosts)

  # now do the same for the instructional machines if we have any:
  if 'machine_list' in deploy_threading.thread_communications.keys():
    connect_and_do_work(deploy_threading.thread_communications['machine_list'], 3)
  

  # if we had unreachable hosts..    
  if deploy_threading.has_unreachable_hosts():
    # Currently, set NOT to retry hosts.  Since it's running regularly as a service,
    # there is no need as 99% of these hosts time out anyway, so it just takes
    # a lot longer than it should. 
    for i in range(0):      
      
      # increase timeout time by 25% each time
      deploy_network.default_connection_timeout =\
          str(int(float(deploy_network.default_connection_timeout) * 1.25))
      
      # 1. use list of unreachable hosts list as our list to retry
      last_failed_hosts = deploy_threading.thread_communications['unreachable_host']

      # 2. reset the unreachable hosts list
      deploy_threading.thread_communications['unreachable_host'] = []
      deploy_logging.log("Notice", "Trying to connect to failed hosts (connection attempt #"+str(i+2)+")")
      connect_and_do_work(last_failed_hosts)
  
  
  print "Checking that all child threads/processes are dead..."
  for each_tuple in deploy_threading.thread_communications['running_process_ids']:
    try:
      # tuple is (pid, expiretime, remotehost, username)
      procid = int(each_tuple[0])
      os.kill(procid, 9)
    except OSError, ose:
      pass
    except Exception, e:
      print "Something went wrong while trying to kill process "+\
          str(procid)+", "+str(e)
  
  deploy_logging.log("Info", "Seeing if there exist instructional machines we need to cleanup still...")
  
  # do we have any instructional machines?
  if 'instructional_machines' in deploy_threading.thread_communications.keys():
    for instructional_machine in deploy_threading.thread_communications['instructional_machines']:
      threadable_cleanup_final(instructional_machine)
  
  print 'Finished.'
  deploy_logging.log("Info", "All threads completely finished...")
  return

  
  
def connect_and_do_work(myhosts, max_threads = deploy_threading.threadsmax):
  """
  <Purpose>
    Does the actual distribution of nodes within max_threads. myhosts is 
      a list of tuples, and so we pop one and pass it off to a thread until
      we have max_threads running, and if one of them is done while we've
      still got more nodes to process we'll launch another new thread.

  <Arguments>
    myhosts:
      list of tuples containing (username, remote_host). The format is the 
      same as returned when the list of IPs is read from file
    max_threads:
      Max # of threads to launch.

  <Exceptions>
    Exception on trouble starting a thread.

  <Side Effects>
    Blocks until all threads are finished.

  <Returns>
    None.
  """
  
  if myhosts:
    deploy_threading.start_thread(threadable_process_node, myhosts, max_threads)
    
    # no more hosts! (let's block until all threads are done)
    running_threads = deploy_threading.threading_currentlyrunning()
    
    # spin until all threads are done..
    while running_threads:
      time.sleep(30)
      helper_print_processing_threads()
      running_threads = deploy_threading.threading_currentlyrunning()

      
    # reset kill flag for the thread monitoring status of the timeouts
    deploy_threading.thread_communications['kill_flag'] = True

  return

  
  
def helper_humanize_nodelist(node_list):
  # just converts (user, hostname) tuple list to user@hostname string
  humanized = ''
  for node in node_list:
    humanized += helper_humanize_node(node)+', '
  # fence post problem. just strip off the last two characters which should 
  # be a space and a comma
  return humanized[0:-2]

  
  
def helper_humanize_node(node):
  """
  <Purpose>
     Converts node (in tuple/list format) to a human readable format

  <Arguments>
    node: first element is the username, second is the remote_host

  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    None.
  """
  user = node[0]
  remote_host = node[1]
  return user+'@'+remote_host
  
  

def helper_print_processing_threads():
  """
  <Purpose>
     Helper that periodically lets us know how many threads are running and
      which nodes they're responsible for

  <Arguments>
    None.

  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    None.
  """
  print 'There are still some threads spinning.'
  print 'Currently, there are some'+\
      ' threads running ('+str(len(deploy_threading.thread_communications['hosts_left']))+' hosts left)',
  print helper_humanize_nodelist(deploy_threading.thread_communications['hosts_left'])

    

def threadable_process_node(node_list):
  """
  <Purpose>
    The parent function that calls child functions to do the little work. From
    this function we can see the order of events:
      1. upload tar
      2. check that we got a response (if not add to unreachable for later)
      3. run cleaning/setup scripts on remote machine
      4. run actual test scripts on remote machine
          (files are grabbed after all scripts execute, called from step4)

  <Arguments>
    node_list:
      a list containing a single tuple of (user, remotehost)

  <Exceptions>
    None.

  <Side Effects>
    Modifies running thread counter.

  <Returns>
    None.
  """
  
  try:

    # node is a list containing one tuple
    node = node_list[0]

    # upload the .tar file.
    # attempt to upload the .tar file to the computers. this'll modify a list of
    # computers that we didn't connect to succesfully,so we'll remove them from
    # the list of computers we want to run the rest of the scripts on.

    threadable_remote_upload_tar(node_list)

    # only continue if node was marked reachable
    if deploy_threading.node_was_reachable(node):
      # clean the node
      threadable_remote_cleanup_all(node_list)
      # run the scripts remotely now
      threadable_remote_run_all(node_list)
      # cleanup the files, but only if it's not an instructional machine
      # the reason for this is because it's NFS and files could still be
      # in use by the other machines. we'll add this to a special list
      # in our thread_communications dict and we'll then clean these up
      # when all threads are totally done
      if not node[1].startswith('128.'):
        threadable_cleanup_final(node_list)
      else:
        # check if array exists already
        deploy_threading.add_instructional_node(node)
        
    # decrement # of threads running
  except Exception, e:
    deploy_logging.logerror("Error in thread assigned to "+node[1]+\
        " threadable_process_node ("+str(e)+")")

    
    
def threadable_cleanup_final(remote_machines):
  """
  <Purpose>
    Cleans the files created by this script from the remote machine
    
  <Arguments>
    remote_machines:
      a list containing a single tuple of (user, remotehost)

  <Exceptions>
    None.

  <Side Effects>

  <Returns>
    None.
  """
  # Assume single element if it's not a list
  if type(remote_machines) != type([]):
    remote_machines = [remote_machines]
  
  # for every machine in our list...
  for machine_tuple in remote_machines:
    
    username = machine_tuple[0]
    machine = machine_tuple[1]

    deploy_logging.log('Final cleanup', 'Final cleanup of  '+machine)

    # build up our list of files/folders we need to delete
    cmd_list = []
    cmd_list.append('rm -rf runlocaltests.py')
    cmd_list.append('rm -rf hashes.dict')
    cmd_list.append('rm -rf '+machine+'.deployrun.log')
    cmd_list.append('rm -rf '+machine+'.deployrun.err.log')
    cmd_list.append('rm -rf testprocess.py')
    cmd_list.append('rm -rf verifyfiles.mix')
    cmd_list.append('rm -rf '+machine+'.tgz')
    cmd_list.append('rm -rf deploy.tar')
    cmd_list.append('rm -rf cleanup_deploy.py')
    #TODO: cleanup custom scripts as well here?
    
    # merge the commands into a string that we'll execute
    cmd_str = '; '.join(cmd_list)
    ssh_stdout, ssh_stderr, ssh_errcode = deploy_network.remote_shellexec(cmd_str, username, str(machine))

    deploy_logging.print_to_log('Detailed cleanup', ssh_stdout, 
        ssh_stderr, ssh_errcode)
  return
  
  
  
def threadable_remote_upload_tar(remote_machines):
  """
  <Purpose>
    Uploads the deploy.tar to each machine before running anything. Machines
      that timeout are added to the unreachable_hosts list in the dictionary.

  <Arguments>
    remote_machines:
      list of tuples with (user, ip) IPs that we have to cleanup.

  <Exceptions>
    None.

  <Side Effects>
    Temporarily locks thread_communications dict which is used by other threads trying
    to upload (if they run into an error).

  <Returns>
    None.
  """

  # Assume single element if it's not a list
  if type(remote_machines) != type([]):
    remote_machines = [remote_machines]
  
  # for every machine in our list...
  for machine_tuple in remote_machines:
    
    # split up the tuple
    username = machine_tuple[0]
    machine = machine_tuple[1]

    deploy_logging.log('Setup', 'Attemping tar file upload via scp on '+machine)
    scp_errcode, scp_stdout, scp_stderr = upload_tar(username, str(machine))

    out, err = deploy_logging.format_stdout_and_err(scp_stdout, scp_stderr)

    # check the error codes
    if str(scp_errcode) == '0':
      deploy_logging.log('Setup', ' scp file upload complete on '+machine)
    elif str(scp_errcode) == '1':
      deploy_logging.logerror('Could not establish a connection with '+machine+' ('+err+')')
      deploy_threading.add_unreachable_host((username, machine))
    else:
      deploy_logging.logerror('scp returned unknown error code '+str(scp_errcode)+' ('+err+')')
      deploy_threading.add_unreachable_host((username, machine))


def threadable_remote_cleanup_all(remote_machines):
  """
  <Purpose>
    Calls remote_runcleanup for each machine in remote_machines.

  <Arguments>
    remote_machines:
      list of tuples with (user, ip) IPs that we have to cleanup.

  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    None.
  """
  # Assume single element if it's not a list
  if type(remote_machines) != type([]):
    remote_machines = [remote_machines]
  
  # for every machine in our list...
  for machine_tuple in remote_machines:
    
    username = machine_tuple[0]
    machine = machine_tuple[1]


    deploy_logging.log('Cleanup/Setup', "Attempting to ssh and run cleaning scripts on "+\
        machine)
    # Run the remote cleanup script
    deploy_network.remote_runcleanup(username, str(machine))
    deploy_logging.log('Cleanup/Setup', " ssh and run cleanup scripts done on "+machine+\
        ". Moving on.")


def threadable_remote_run_all(remote_machines):
  """
  <Purpose>
    This function connects to the remote computer and executes the 
    actual test scripts.

    This function is run_func threadable

  <Arguments>
    remote_machines:
      list of tuples with (user, ip) that we'll run our tests on.

  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    None.
  """

  # Assume single element if it's not a list
  if type(remote_machines) != type([]):
    remote_machines = [remote_machines]

  # For every single machine we're assigned...
  for machine_tuple in remote_machines:
    # Run the files remotely
    username = machine_tuple[0]
    machine = machine_tuple[1]
    deploy_logging.log('Info', "Attempting to ssh and run scripts on "+machine+"...")
    deploy_network.remote_runscript(username, str(machine), custom_script_name)
    deploy_logging.log('Info', "Running scripts on "+str(machine)+" completed. Moving on.")



# main() handles all the cool things we're about to do :)
if __name__ == "__main__":
  main()
