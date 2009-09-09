"""
<Program Name>
  runlocaltests.py

<Started>
  May 2009

<Author>
  n2k8000@u.washington.edu
  Konstantin Pik

<Purpose>
  Executes test files from deploy.tar. This file is not to be used by itself, 
  but instead should be packaged in deploy.tar (which is all performed by the
  deploy.py script). This runs on the remote machine, and assumes that the 
  deploy.tar is in the same directory.

<Usage>
  Note: Not indended to run as a standalone (but can be).

  python runlocaltests.py myhostname [-v 0|1|2] [scriptname]

  myhostname:   Required. The hostname of this computer. Used for some path
                  information (logs, etc).
  -v:           Optional. Sets verbosity level.
                  0: Default. log only other scripts
                  1: log other scripts + this script
                  2: very verbose: log all other + this + console output
                  all other values default to 0
  scriptname:   Optional. Default None.  Additional script file to execute.
                  This must be a python script (TODO: add .sh script capability)
"""

import os
import sys
import time
import subprocess
import thread

# used to keep track of how long it took the script to run
start_time = 0

# the name of custom script to run, if needed
custom_script_name = ''

# only run the custom script?
only_custom_script = False

# the hostname of this computer as seen by intiating script
my_host_name = ''

# Verbosity flag (0, 1, 2)
verbosity = 0

# Lock on the log file. There isn't any multi threading in this file
# but just in case I put this here.
filelock = thread.allocate_lock()

# This file will traverse multiple directories and search for seattle
# installs.  This variable changes the path to each install directory.
logdir = ''


# The of the seattle_install file: typically either .tar or .tgz TODO: remove
seattle_linux_ext = ''

def find_seattle_installs():
  """
  <Purpose>
    Finds all seattle install directories. (cares only about the first
      one found)

    Priority:
      1. ./seattle_repy folder (exit after find)
      2. ./[remotehost]/seattle_repy folder (exit after find)
      3. search ALL folder with search depth 1 for a seattle_repy folder

    Also assumes that seattle_repy is the name of the install directory.
     
  <Arguments>
    None.
    
  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    A list containing the path to the folder containing seattle_repy install
  """
  global my_host_name

  # This will keep track of which folders have a seattle installation
  valid_folder = []

  log("Checking for seattle_repy directory..")

  # Check for seattle_repy dir from where we are now.. 
  if os.path.isdir("./"+my_host_name+"/seattle_repy"):
    log("Good news! seattle_repy found in "+my_host_name+". Not searching anywhere else.")
    valid_folder.append("./"+my_host_name+"/seattle_repy")
  elif os.path.isdir("./seattle_repy"):
    log("Good news! Found seattle_repy in $HOME Not looking anywhere else.")
    valid_folder.append("./seattle_repy")
  else:
    # search each folder in current directory
    log("NOTICE: seattle_repy not found in default directories.. Searching local folders.")
    # otherwise check all folders with depth one.
    for folder in os.listdir('.'):
      # if inside that folder we have a seattle install, add it to our list
      if os.path.isdir("./"+folder+"/seattle_repy"):
        log("Found seattle install in "+folder)
        valid_folder.append("./"+folder+"/seattle_repy")
        return valid_folder
  
  # return list (with one element, the path) folder with a seattle_install
  return valid_folder


  
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

  

def logerror(data):
  """
  <Purpose>
    Wrapper to log to an error log file, and prints to console in case we're 
      not in -v 2 mode.
     
  <Arguments>
    data:
      The error description/etc.
    
  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    No returns.
  """
  global verbosity, logdir, my_host_name

  # print only if not -v 2.. dont want to spam stdout more than we already are
  if verbosity < 2:
    print 'ERROR:'+str(data)

  # change logdir to '' so we log to our main error log file, then we'll 
  # change it back to the directory we were working with
  logdir_temp = logdir
  logdir = ''
  log(my_host_name+': Error: '+data+'(logdir: '+logdir_temp+')', False, True, '', 'deployrun.err')
  logdir = logdir_temp
  return

  
  
def log(data, sep=False, timestamp=False, scriptdesc='[runlocaltests.py] ', fn='deployrun'):
  """
  <Purpose>
    Logs data to a file.
     
  <Arguments>
    data: The data to log.
    sep:  Optional. Default is False. Is this a separator string?
    timestamp:  Optional. Default is False. Timestamp this msg?
    scriptdesc: Optional. Description of the msg (appended to front of msg)
    fn: Optional. Default is deploy.run. The log file name. Unless you're 
          adding functions to this .py file, it's not recommended you change
          the log file name. 

    IMPORTANT: this will always log to [myhostname].[fn].log
        fn -> parameter/filename
        myhostname -> hostname of this computer as seen by others
    
  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    None.
  """
  global verbosity
  global filelock
  global logdir
  global my_host_name

  # lock the log file
  filelock.acquire()

  # logdir path variable isn't empty then use it
  if logdir:
    logfile = open(logdir+'/deploy.logs/'+fn+'.log', 'a')
  else: # otherwise log to default dir with default file name
    logfile = open(my_host_name+'.'+fn+'.log', 'a')

  # We're going to build up the string we're going to log
  logstring = ''
  
  # Write separator if flag is set
  if sep :
    # there is no custom separator to use, use the default
    if data == '':
      logstring = '\n------------------------------------------------------------------------'
    else: # custom separator specified
      logstring = '\n'+data
  
  # if it's not a separator then process rest of args
  if not sep:
    # if our verbosity is 0 then script must not be runlocaltests.py
    # or our verbosity has to be greater than 1
    # if verbosity == 1, then scriptdesc MUST be blank (means it's a 
    # foreign script)
    if (verbosity == 1 and scriptdesc == '') or (verbosity == 0 and 
      scriptdesc != '[runlocaltests.py] ') or (verbosity == 2): 
        logstring += '\n'

        # do we need a timestamp?
        if timestamp:
          logstring += get_current_time()+" | "
        
        logstring += scriptdesc+str(data)

  # if our string isn't empty by this time then...
  if logstring.strip('\n '):
    # on verbosity == 2, we print to stdout as well. 
    # NOTE: THIS HAS THE POTENTIAL TO MAKE YOUR LOGS LARGE AS
    # ALL OUTPUT WILL BE DOUBLE.. STDOUT WILL BE LOGGED AS WELL 
    # AS THE LOG FILE (on the calling machine)
    if verbosity == 2:
      print my_host_name+': '+logstring.strip('\n ')
 
    logfile.write(logstring)



  logfile.close()

  filelock.release()
  return

  
  
def is_locked(pathtodir):
  # OBSOLETE
  """
  <Purpose>
    Checks whether a directory was locked with lock_dir().
    
  <Arguments>
    pathtodir
      Path to the directory to check.
    
  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    A tuple:   (Locked, ValidDirectory, DescriptionString)
    
    Detailed
    Locked: Boolean. Is the directory locked?
    Valid: Boolean. Is this a valid directory?
    DescriptionString: String. A human readable response to whether we
                        obtained a lock or not, and why.
  """
  return (False, True, 'Obsolete')
  #checks whether a dir has a lock
  if os.path.isdir(pathtodir):
    # yes it is a dir.. now check if there's a lock file
    if not os.path.isfile(pathtodir+'/DIR.lock'):
      return (False, True, 'No lock file in directory')
    # is a directory, but file exists
    return (True, True, 'Lock file exists in directory')
  else:
    # invalid dirs result in lock = true as far as we're concerned.
    return (True, False, 'Not a valid directory')

    
    
def lock_dir(pathtodir):
  # OBSOLETE
  """
  <Purpose>
    "Locks" a directory by creating a .LOCK file in it.

    This prevents multiple instances of a script from messing with the same
    directory at the same time.
    
  <Arguments>
    pathtodir
      Path to the directory to lock.
    
  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    Boolean. Did we successfully lock the directory?
  """
  return True
  # We'll use this as our flag on whether we succeeded or not.
  return_status = False

  # is it a directory?
  if os.path.isdir(pathtodir):
    # yes! make a file
    try:
      lock_handle = open(pathtodir+'/DIR.lock', 'w')
      lock_handle.write('\n')
    except Exception, e:
      logerror('Something went wrong while locking '+pathtodir)
    else: # no exception
      return_status = True
    finally:
      lock_handle.close()

  return return_status


  
def shellexec(cmd_str):
  """
  <Purpose>
    Uses subprocess to execute the command string in the shell.
     
  <Arguments>
    cmd_str:  The string to be treated as a command (or set of commands,
                separated by ;).
    
  <Exceptions>
    None.

  <Side Effects>
    Sometimes on NFS, a file may be 'shared' amongst different computers
    (since all file uploads are to ~/), so if we get a NFS error, we'll sleep
    and then try executing our command again.

  <Returns>
    A tuple containing (stdout, strerr)

    Detailed:
    stdout: stdout printed to console during command execution.
    strerr: error (note: some programs print to strerr instead of stdout)
  """
  global verbosity
  # get a handle to the subprocess we're creating..
  handle = subprocess.Popen(cmd_str, shell=True, 
      stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

  # execute and grab the stdout and err
  stdoutdata, strerrdata = handle.communicate("")
  
  # this is a hack, but if we run into a stale NFS file handle, then sleep 2-3
  # seconds, and try to execute command again. we'll put this in a loop, so we can
  # do this up to three times
  retries_left = 3

  # set flag so we enter our loop
  staleNFS = True

  while(retries_left > 3 and staleNFS):
    if retries_:
      # check both out and err for the string indicating stale NFS file handle
      stdout_has_err = stdoutdata.find('Stale NFS file handle') > -1
      strerr_has_err = strerrdata.find('Stale NFS file handle') > -1
      if stdout_has_err or strerr_has_err:
        # stale :(
        time.sleep(2)
        # retry the command.
        handle = subprocess.Popen(cmd_str, shell=True, 
          stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # execute and grab the stdout and err
        stdoutdata, strerrdata = handle.communicate("")
        # decrease times we can retry the command
        retries_left -= 1
      else:
        # no more staleNFS!
        staleNFS = False

  # If we're really verbose, then log the exact command string we executed.
  if verbosity == 2:
    log(cmd_str)

  return stdoutdata, strerrdata 

  
  
def loghelper(stdout, stderr):
  """
  <Purpose>
    Helper for the log method. This just formats stdout and stderr before
    passing it off to log().  Esentially strips off excess trailing \n's and spaces.
     
  <Arguments>
    stdout: out to format.
    stderr: err to format.

  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    None.
  """

  # log stdout
  stdout = stdout.strip('\n ')
  stderr = stderr.strip('\n ')

  # The 4th parameter='' so it always logs all output regardless of verbosity
  # Log only if not empty...
  if stdout:
    log(stdout.strip(), False, False, '')
  if stderr:
    log(stderr.strip(), False, False, '')

    

def start_timer():  
  """
  <Purpose>
    This sets the current time to be used in keeping track of how long the 
    script's been running.
     
  <Arguments>
    None.
    
  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    None.
  """

  global start_time
  start_time = time.time()
  return

  
  
def stop_timer():
  """
  <Purpose>
    This stops the time keeping track of how long the script's been running.
     
  <Arguments>
    None.
    
  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    The elapsed time in seconds.
  """

  global start_time
  return (time.time() - start_time)

  
 
def kill_hung_testprocess_module():
  """
  <Purpose>
    This is a workaround for killing hung testprocess.py modules that did not 
    have a clean exit.
     
  <Arguments>
    None.
    
  <Exceptions>
    None.

  <Side Effects>
    Kills all running modules that have the string testprocess.py in their name.

  <Returns>
    None.
  """
  # lists all processes, finds ones that have the testprocess.py string, 
  # eliminates anything with the grep string, the awk command line prints out th PID
  # and xargs pipes the PID to kill via command line.
  shellexec("ps -ef | grep testprocess.py | grep -v grep | awk '{ print $2 } ' | xargs kill -9")
  
 
  
def start_scripts(folder_list):
  """
  <Purpose>
    This initiates the checking of the list of discovered seattle install
    folders by extracting and executing each script.
     
  <Arguments>
    folder_list:  the list of folders that contain installs of seattle
    
  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    None.
  """
  global logdir, seattle_linux_ext, custom_script_name, only_custom_script
  
  # the following kills the testprocess module that may be hung from previous timeouts.
  kill_hung_testprocess_module()
  
  
  # cmd list is our general command list that we will use for each directory
  # by replacing $INSTALL with the path to the installation directory.
  # then in the for loop we execute each command by index number
  cmd_list = []

  # 0. Untar the three files (two scripts, and one dictionary that'll
  #     be used to verify file hashes.
  cmd_list.append('tar -xf deploy.tar testprocess.py verifyfiles.mix hashes.dict deploy_helper.py')

  # 1+2. move the two files to install directory
  cmd_list.append('cp testprocess.py $INSTALL/testprocess.py')
  cmd_list.append('cp verifyfiles.mix $INSTALL/verifyfiles.mix;'+\
    'cp hashes.dict $INSTALL/hashes.dict; cp deploy_helper.py $INSTALL/deploy_helper.py')


  # 3. Change dir because python will look in cwd when executing repypp.py
  #     and as a result the files required for the 'include' statements
  #     run repypp.py on verifyfiles.mix
  cmd_list.append('cd $INSTALL; python repypp.py verifyfiles.mix '+\
    'verifyfiles.py')

  # 4. run the first test script
  cmd_list.append('python $INSTALL/testprocess.py')
  
  # 5. run the second test script 
  #  Note that we need to cd to $INSTALL and one above it directory because
  # of the way that verifyfiles.py is written - starts checking in local 
  # directory for scripts. then we need to assume that the .tar containing the
  # install is in our home path (which it should be).
  cmd_list.append('cd $INSTALL; python verifyfiles.py '+\
    '-readfile hashes.dict ../')
  
  # 6+7+8. do we have a custom script? << This is still in progress.
  if custom_script_name:
    cmd_list.append('tar -xf deploy.tar '+custom_script_name)
    cmd_list.append('cp '+custom_script_name+' $INSTALL/'+custom_script_name)
    cmd_list.append('python $INSTALL/'+custom_script_name+' $INSTALL')

  # enumerate through each folder path now
  for folder in folder_list:
    # check if folder is locked
    # if a folder is locked then another deploy-checking script is using this folder
    # and we just skip through it.
    islocked, validdir, dscrptn_str = is_locked(folder)    

    # The directory needs to be 'unlocked' (no other script is checking that
    # folder now and if it is then we'll go through with our check of that 
    # folder
    if islocked: # locked.
      if validdir: # and a valid directory path
        logerror('Directory '+folder+' is locked. Moving on.')
      else:
        # this means that it's an invalid directory. Should technically 
        # never hapnd if the script is running by itself as it auto-discovers
        # directories and stores them properly. This *might* occur if a 
        # directory is being modified/renamed/deleted WHILE the script is
        # running (which this script does not do).
        logerror('Directory '+folder+' is an invalid path. Moving on.')
    else: # no lock found!

      # try to lock the folder
      locked_successfully = lock_dir(folder)

      if not locked_successfully: # coudln't lock folder..
        logerror('Locking '+folder+'. Moving on.')
      else: # folder locked successfully, start the beefy chunks..
        # Check if we only need to run the custom test file, or all the scripts
        if not only_custom_script:
          
          # setup a log dir for that install
          log('Creating log directory in '+folder)
          shellexec('mkdir '+folder+'/deploy.logs')

          # set the logdir global so we can start logging in that folder.
          logdir = folder

          log('=============Running from folder:'+folder, True, False, '')

          # NOTE: Please see above what each index means in more detail
          stdoutdata, stderrdata = shellexec(cmd_list[0])
          loghelper(stdoutdata, stderrdata)
          log("Untarred testprocess.py verifyfiles.mix successfully")

          # the .replace's below just replace $INSTALL with the folder we're 
          # dealing with

          stdoutdata, stderrdata = shellexec(cmd_list[1].replace('$INSTALL', folder))
          loghelper(stdoutdata, stderrdata)
          stdoutdata, stderrdata = shellexec(cmd_list[2].replace('$INSTALL', folder))
          loghelper(stdoutdata, stderrdata)
          log("Moved files into $INSTALL sucessfully".replace('$INSTALL', folder))
          
          log("Attempting to run repypp.py on verifyfiles.mix...")
          stdoutdata, stderrdata = shellexec(cmd_list[3].replace('$INSTALL', folder))
          loghelper(stdoutdata, stderrdata)
          log("repypp executed sucessfully.")  


          log("Running testprocess.py", False, False)
          stdoutdata, stderrdata = shellexec(cmd_list[4].replace('$INSTALL', folder))
          loghelper(stdoutdata, stderrdata)
          
          log("Running verifyfiles.py", False, False)
          stdoutdata, stderrdata = shellexec(cmd_list[5].replace('$INSTALL', folder))
          # there'll be 4 lines that we need to strip from output because they'll always 
          # marked as 'unknown files' but we know they're safe. Log them only in v = 2
          if verbosity < 2:
            stdoutdata = stdoutdata.replace('testprocess.py:Warning:Unknown file\n', '')
            stdoutdata = stdoutdata.replace('verifyfiles.py:Warning:Unknown file\n', '')
            stdoutdata = stdoutdata.replace('verifyfiles.mix:Warning:Unknown file\n', '')
            stdoutdata = stdoutdata.replace('DIR.lock:Warning:Unknown file\n', '')
            stdoutdata = stdoutdata.replace('hashes.dict:Warning:Unknown file\n', '')
          loghelper(stdoutdata, stderrdata)
        
        # one more script to run.
        if custom_script_name:
          log("Running custom script ("+custom_script_name+"):", False, False, '')
          stdoutdata, stderrdata = shellexec(cmd_list[6].replace('$INSTALL', folder))
          loghelper(stdoutdata, stderrdata)
          stdoutdata, stderrdata = shellexec(cmd_list[7].replace('$INSTALL', folder))
          loghelper(stdoutdata, stderrdata)
          stdoutdata, stderrdata = shellexec(cmd_list[8].replace('$INSTALL', folder))
          loghelper(stdoutdata, stderrdata)


        log('Cleaning up and moving on...')
        # Try to delete the files we were using so that we don't leave
        # any junk behind
        try:
          if os.path.isfile(folder+'/verifyfiles.mix'):
            os.remove(folder+'/verifyfiles.mix')
          if os.path.isfile(folder+'/verifyfiles.py'):
            os.remove(folder+'/verifyfiles.py')
          if os.path.isfile(folder+'/testprocess.py'):
            os.remove(folder+'/testprocess.py')
          if os.path.isfile(folder+'/deploy_helper.py'):
            os.remove(folder+'/deploy_helper.py')
          if custom_script_name and os.path.isfile(folder+'/'+custom_script_name):
            os.remove(folder+'/'+custom_script_name)
        except Exception, e:
          logerror("Error cleaning temp files from "+folder+"("+str(e)+")")
          continue # Don't stop! keep going
        # reset logdir to mainlog file
        # logdir = ''



def init_setup():
  """
  <Purpose>
    Calls list of methods that cannot fail. If we can't set up our environment
    then return false.

  <Arguments>
    None.
    
  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    Boolean. Did all the setup scripts succeed?
  """
  # Currently empty.

  return True
  
  

def main(args):
  """
  <Purpose>
    Entry point into the script. This checks that all the parameters are
    correctly specified and the script is called validly. Next, it finds the
    seattle_repy directory and moves scripts there, then calls the custom 
    script (if one exists) and passes in one argument: the path to the 
    seattle_install.

    Note: it is important that your custom script must use absolute paths
    to the install directory.

  <Arguments>
    None.
    
  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    None.
  """
  start_timer()
  #  runlocaltests.py myhostname [-v 0|1|2] [customscriptname]
  global verbosity
  global logdir
  global my_host_name
  global custom_script_name
  global only_custom_script
  
  # Method that sets up the environment (verbosity, custom scripts, etc)
  if args and len(args) >= 2:
    my_host_name = args[1]
    if len(args) >=3: # check for -v flags
      if args[2] == '-v':
        if len(args) >= 4:
          # different verbosity levels
          # 0: default, log only other scripts
          # 1: log other scripts + this script
          # 2: very verbosity: log all other + this + console output
          # all other values default to 0
          verbosity = int(args[3])
          # validate verbosity.
          if verbosity > 2 or verbosity < 0:
            verbosity = 0
          if len(args) >= 5:
            custom_script_name = args[4]
            log('Obtained a custom script to run ('+custom_script_name+')')
          if len(args) >= 6:
            # this last parameter mean we should JUST execute the custom script file
            only_custom_script = True
            log('Only running custom script file')
            
  else: # no args..
    print 'CRITICAL ERROR: HOSTNAME FOR THIS COMPUTER NOT SPECIFIED. EXITING'
    logerror('CRITICAL ERROR: HOSTNAME FOR THIS COMPUTER NOT SPECIFIED. EXITING')
    logerror('Elapsed time'+str(stop_timer()))
    pack_logs(None)
    return

  print "Verbosity is set to "+str(verbosity)  

  # checking env
  # TODO: provide .dict file
  init_setup()  

  log("Starting up local scripts on "+my_host_name)
  
  # get list of install folders
  seattle_folders = find_seattle_installs()

  if not seattle_folders:
    print "Did not find any seattle installs on "+my_host_name+". Aborting."
    logerror("Did not find any seattle installs on "+my_host_name+". Aborting.")
    logerror('Elapsed time'+str(stop_timer()))
    pack_logs(None)
    return
  
  print "Running local scripts..."
  # Start checking for a seattle install folder
  start_scripts(seattle_folders)

  logdir_old = logdir
  logdir = '' # reset logdir so that we log to default log file
  log("Scripts are done. Begining cleanup...")

  log("Collecting logs...")

  log("Cleanup complete. Exiting")

  # log back to logdir for the install
  logdir = logdir_old
  log('Elapsed execution time for all scripts was '+str(stop_timer())+'s', 
    False, False, '')

  logdir = ''
  pack_logs(seattle_folders)
  return

  
  
def pack_logs(seattle_install_paths):
  """
  <Purpose>
    This method packs all the log files from this machine into a gzipped tar
    and names it [remotehostname].tgz. The calling script (or anyone else) can
    then pick up the file.
    
  <Arguments>
    seattle_install_paths:
      List containing one (1) element which is the path to the seattle install.
    
  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    None.
  """
  # this will pack all the logs in a .tar file and have it ready for pickup
  global my_host_name, verbosity

  # we'll be passed in a list, but there should only be one element
  if seattle_install_paths:
    seattle_install_path = seattle_install_paths[0]

  # this wil keep track of how many file's we're adding to the tar. if zero by
  # the time it's time to execute, then don't make one. This'll make an error
  # in deploy.py and we'll have to check out what went wrong.
  files_added = 0

  # we'll build up a command string to execute to build our tar
  command_string = ''

  # the tar will be named my_host_name.tgz
  if verbosity == 2:
    command_string += 'tar -czvvf '+my_host_name+'.tgz '
  else:
    command_string += 'tar -czf '+my_host_name+'.tgz '

  # add the general logfile only if we're in -v 2, otherwise the file'll have nothing
  if verbosity == 2:
    if os.path.isfile('./'+my_host_name+'.deployrun.log'):
      command_string += ' ./'+my_host_name+'.deployrun.log'
      files_added += 1

  # grab the error file (will exist only if there were errors)
  if os.path.isfile('./'+my_host_name+'.deployrun.err.log'):
    command_string += ' ./'+my_host_name+'.deployrun.err.log'
    files_added += 1

  # grab the info for that seattle install directory (if not None)
  if seattle_install_paths:
    # don't make tar freakout about file not existing (if we errored for some
    # reason)
    if os.path.isfile(seattle_install_path+'/deploy.logs/deployrun.log'):
      command_string += ' -C '+seattle_install_path+'/deploy.logs/ deployrun.log'
      files_added += 1

  if verbosity == 2:
    print my_host_name+': Building tar with logs : '+command_string
  # execute the string! (only if we have more than one file we're adding
  if files_added > 0:
    out, err = shellexec(command_string)

    if out.strip('\n '):
      print out.strip('\n ')
    if err.strip('\n '):
      print err.strip('\n ')
  return

if __name__ == "__main__":
  main(sys.argv)

