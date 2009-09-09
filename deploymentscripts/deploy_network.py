"""
<Program Name>
  deploy_network.py

<Started>
  May 2009

<Author>
  n2k8000@u.washington.edu
  Konstantin Pik

<Purpose>
  This is the file contains network-related functions that are used by the 
  deployment script.  This file is not to be executed by itself, but is to
  be used with deploy_*.

<Usage>
  See deploy_main.py.
  
"""
import os
import subprocess
import thread
import time

import deploy_main
import deploy_logging
import deploy_threading
import deploy_helper


# the default connection timeout time (will increase by 25% after each 
# failed run
default_connection_timeout = '60'


def remote_runscript(user, remote_host, custom_script_name = '', run_custom_only = False, tar_filename = 'deploy.tar'):
  """
  <Purpose>
    This function connects to user@remote_host using the specified rsa key.
    Typically, only the user and remote_host fields need to be changed - the 
    RSA key used is the user's default RSA key.  After connecting, this will
    extract runlocaltests.py from the tar_filename and execute it remotely.
     
  <Arguments>
    user:
      the user to log in as on the remote machine.
    remote_host:
      the remote machine's IP to which we'll be uploading files.
    custom_script_name:
      the name(s) as strings of custom scripts to run on the remote machine.
    run_custom_only:
      Should we only run the custom script?
    tar_filename: 
      Optional. Default is deploy.tar. The tar file to upload to the remote 
        host.
    
  <Exceptions>
    None.

  <Side Effects>
    Blocks current thread until remote script is done executing.

  <Returns>
    No returns.
  """

  # We will build up our list of commands as a list of strings, then 
  # join with the ';' to specifify multiple commands on one line.
  cmd_list = []

  # extract out remote setup script that'll figure out where the files need to 
  # be extracted to
  cmd_list.append('tar -xf '+tar_filename+' runlocaltests.py')


  # The following lines execute the script remotely
  # IMPORTANT - SEE runlocaltests.py for args
  # if verbose flag is set, make the runlocaltests.py script also verbose
  
  if run_custom_only:
    cmd_list.append('python runlocaltests.py '+remote_host+' -v '+\
        str(deploy_main.verbosity)+' '+custom_script_name+' 1')
  else: # tell the script we're ONLY running the custom files
    cmd_list.append('python runlocaltests.py '+remote_host+' -v '+\
        str(deploy_main.verbosity)+' '+custom_script_name)

  # Create the one string that we'll execute, join with '; '
  command_string = '; '.join(cmd_list)

  # use helper to execute command_string on user@remote_host
  out, err, returncode = remote_shellexec(command_string, user, remote_host)

  deploy_logging.print_to_log(remote_host, out, err, returncode)

  # Once we're done executing the remote script, lets grab the logs
  remote_get_log(user, remote_host)



def remote_get_log(user, remote_host):
  """
  <Purpose>
    Gets the remote logs (all tarred up) from remote_host and copies it to a 
    local directory via scp then untars it into deploy.logs/[remote_host]/.

  <Arguments>
    user:
      the user to log in as
    remote_host:
      the IP of the host to get the logs from
    
  <Exceptions>
    scp fails/times out.

  <Side Effects>
    None.

  <Returns>
    No returns.
  """

  try:
    # set up dir that we'll move the remote .tar into
    if not os.path.isdir('./deploy.logs/'+remote_host):
      os.mkdir('./deploy.logs/'+remote_host)
    
    # download the tar file from remote host
    out, err, returncode = remote_download_file(remote_host+'.tgz', 
        './deploy.logs/'+remote_host+'/'+remote_host+'.tgz', user, remote_host)

    deploy_logging.log('Downloading logs', 'Logs downloaded from '+remote_host)
    # now try to untar the files

    # build up a command list to execute
    command_list = []

    # tar is picky about where it'll unzip to (CWD), so we'll just Cd there
    command_list.append('cd ./deploy.logs/'+remote_host+'/')

    # now untar. if deploy_main.verbosity >=1 then we'll be verbose
    if deploy_main.verbosity >=1:
      command_list.append('tar -xvvf '+remote_host+'.tgz')
    else:
      command_list.append('tar -xf '+remote_host+'.tgz')

    # not make command string by joining the list elements with '; '  
    command_string = '; '.join(command_list)

    # execute string
    out, err, retvalue = deploy_helper.shellexec2(command_string)

    deploy_logging.log('Downloading logs', 'Logs from '+remote_host+' are ready')

    # we no longer need the tar file, just hogging up space
    os.remove('./deploy.logs/'+remote_host+'/'+remote_host+'.tgz')

  except Exception, e:
    if deploy_main.verbosity == 2:
      # Only log if we error and need to narrow this down. otherwise,
      # it gets really spammy.    
      deploy_logging.logerror(remote_host+": Some kind of err in remote_get_log. ("+\
          remote_host+") , error:"+str(e)+")")
  return



def remote_runcleanup(user, remote_host):
  """
  <Purpose>
    This function connects to the remote computer and executes the 
    cleanup/setup script.

  <Arguments>
    user:
      the user to log in as
    remote_host:
      the IP of the host to get the logs from

  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    None.
  """

  # build up the command list that we'll execute on the remote host
  cmd_list = []

  # extract the cleanup script
  cmd_list.append('tar -xf deploy.tar cleanup_deploy.py')
  
  # execute the script
  cmd_list.append('python cleanup_deploy.py '+remote_host)

  # join the list together with '; ' between the entries
  cmd_str = '; '.join(cmd_list)
  
  # our handle to the session
  out, err, returncode = remote_shellexec(cmd_str, user, remote_host)

  deploy_logging.print_to_log('Cleanup/Setup', out, err, returncode)
    


def remote_shellexec(command_string, user, remote_host, retry_on_refusal = 3, connect_timeout = default_connection_timeout):
  """
  <Purpose>
    This uses ssh to execute the command_string on user@remote_host.
     
  <Arguments>
    command_string:
      the command string we'll execute on the remote machine. Commands are 
      executed sequentially.
    user:
      user to log in as
    remote_host:
      the ip/name of the machine we're connecting to.
    retry_on_refusal:
      Optional. Integer. Has number of times to retry the connection IF it was
      refused (built in to take care of not 'spamming' the remote server)
    connect_timeout:
      Optional. String. Time in seconds for ssh to timeout if no response was
      received.
    
  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    Tuple. (out, err, returncode)
    Details:
      out: stdout from ssh
      err: err from ssh
      returncode: ssh's exit code
  """

  # execute the string on the remote computer by sshing

  # ssh_proc is the handle to our ssh session process
  # -T is needed because otherwise you get a weird error from ssh (even though
  # everything executes flawlessly. -T specifies not allocate a tty (which
  # is fine for our purposes. -i specifies rsa priv key file path
  # StrictHostKeyChecking=no tells ssh to connect to the remote host even if 
  # the remote host's ip is not trusted (cached) in known_hosts file.
  
  ssh_proc_handle = subprocess.Popen('ssh -T -o BatchMode=yes -o ConnectTimeout='+\
      str(connect_timeout)+' -o StrictHostKeyChecking=no '\
      ' '+user+'@'+remote_host, shell=True, stdin=subprocess.PIPE,
      stdout=subprocess.PIPE, stderr=subprocess.PIPE)

  # get the process ID
  ssh_proc_pid = ssh_proc_handle.pid

  # start thread to monitor timeouts (on another thread)
  deploy_threading.monitor_timeout(ssh_proc_pid, int(connect_timeout), remote_host, user)

  # execute string and block this thread until done...
  out, err = ssh_proc_handle.communicate(command_string)

  returncode = ssh_proc_handle.returncode

  # retry if conn. was refused? (if we have retries left)
  if retry_on_refusal:
    # check if we got a connection refused. if we did, could be cuz we're 
    # spamming the server, so sleep and then try again
    didwesleep = sleep_on_conn_refused(out, err, retry_on_refusal, remote_host)
    # we slept, so call function again and try to execute
    if didwesleep:
      # run again, but this time decrement retry counter
      out, err, returncode = remote_shellexec(command_string, user, 
          remote_host, retry_on_refusal - 1, connect_timeout)

  # format the string
  out, err = deploy_logging.format_stdout_and_err(out, err)

  return out, err, returncode



def remote_download_dir(remote_source_dir, local_dest_dir, user, remote_host, retry_on_refusal = 3, connect_timeout = default_connection_timeout):
  """
  <Purpose>
    This uses scp to download a directory from a remote computer.
     
  <Arguments>
    remote_source_dir:
      The path to the directory to download (remote directory)
    local_dest_dir:
      Where do we put it on this computer?
    user:
      user to log in as
    remote_host:
      the ip/name of the machine we're connecting to.
    retry_on_refusal:
      Optional. Integer. Has number of times to retry the connection IF it was
      refused (built in to take care of not 'spamming' the remote server)
    connect_timeout:
      Optional. Integer. Time in seconds for ssh to timeout if no response was
      received.
    
  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    Tuple. (out, err, returncode)
    Details:
      out: stdout from scp
      err: err from ssh
      returncode: scp's exit code
  """
  # the dir one level 'up' from the our destination dir must exist, so lets 
  # grab it by doing some string math.. remove trailing . and then partition
  local_dest_dir_parent, junk, morejunk = local_dest_dir.strip('/').rpartition('/')  

  # if our local destination directory does not exist then complain.
  if not os.path.isdir(local_dest_dir_parent):
    deploy_logging.logerror(local_dest_dir)
    deploy_logging.logerror(local_dest_dir_parent)
    deploy_logging.logerror('Problem with local directory: it does not exist!')
    raise Exception('Please check calling method.')

  # get the scp handle
  scp_proc_handle = subprocess.Popen('scp -r -o BatchMode=yes -o '+
      'ConnectTimeout='+str(connect_timeout)+' -o StrictHostKeyChecking=no '+\
      user+'@'+remote_host+':'+remote_source_dir+\
      ' '+local_dest_dir, shell = True, stdout = subprocess.PIPE, 
      stderr = subprocess.PIPE)  
    
  # the pid of the scp process just started
  scp_proc_pid = scp_proc_handle.pid

  # start thread to monitor timeouts (on another thread)
  deploy_threading.monitor_timeout(scp_proc_pid, int(connect_timeout), remote_host, user)

  # execute string and block this thread until done...
  out, err = scp_proc_handle.communicate('')

  returncode = scp_proc_handle.returncode

  # retry if conn. was refused?
  if retry_on_refusal:
    # check if we got a connection refused. if we did, could be cuz we're 
    # spamming the server, so sleep and then try again
    didwesleep = sleep_on_conn_refused(out, err, retry_on_refusal, remote_host)
    # we slept, so call function again and try to execute
    if didwesleep:
      # run again, but this time decrement retry counter
      out, err, returncode = remote_download_dir(remote_source_dir, 
          local_dest_dir, user, remote_host, retry_on_refusal - 1, 
          connect_timeout = default_connection_timeout)

  # format the string
  out, err = deploy_logging.format_stdout_and_err(out, err)

  return out, err, returncode



def remote_download_file(remote_fn_path, local_fn_path, user, remote_host, retry_on_refusal = 3, connect_timeout = default_connection_timeout):
  """
  <Purpose>
    This uses scp to download a file from a remote computer.
     
  <Arguments>
    remote_fn_path:
      The path to the file to download (remote file)
    local_fn_path:
      Where do we put it on this computer?
    user:
      user to log in as
    remote_host:
      the ip/name of the machine we're connecting to.
    retry_on_refusal:
      Optional. Integer. Has number of times to retry the connection IF it was
      refused (built in to take care of not 'spamming' the remote server)
    connect_timeout:
      Optional. Integer. Time in seconds for ssh to timeout if no response was
      received.
    
  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    Tuple. (out, err, returncode)
    Details:
      out: stdout from scp
      err: err from ssh
      returncode: scp's exit code
  """
  # local_fn_path will have the path + name of file

  # get the fn by doing some string math..
  dir_to_local_file, junk, localfn = local_fn_path.rpartition('/')  

  # is the dir real?
  if not os.path.isdir(dir_to_local_file):
    deploy_logging.logerror('Local destination directory does not exist.')
    raise Exception('Please check calling method.')

  # the SCP handle used
  scp_proc_handle = subprocess.Popen('scp -o BatchMode=yes -o '+\
      'ConnectTimeout='+str(connect_timeout)+' -o StrictHostKeyChecking=no '+\
      ' '+user+'@'+remote_host+':'+remote_fn_path+\
      ' '+local_fn_path, shell = True, stdout = subprocess.PIPE, 
      stderr = subprocess.PIPE)    
  
  # set the PID of the process so we can set a timeout later
  scp_proc_pid = scp_proc_handle.pid

  # start thread to monitor timeouts (on another thread)
  deploy_threading.monitor_timeout(scp_proc_pid, int(connect_timeout), remote_host, user)

  # execute
  out, err = scp_proc_handle.communicate('')

  returncode = scp_proc_handle.returncode

  # retry if conn. was refused?
  if retry_on_refusal:
    # check if we got a connection refused. if we did, could be cuz we're spamming
    # the server, so sleep and then try again
    didwesleep = sleep_on_conn_refused(out, err, retry_on_refusal, remote_host)
    # we slept, so call function again and try to execute
    if didwesleep:
      # run again, but this time decrement retry counter
      out, err, returncode = remote_download_file(remote_fn_path, 
          local_fn_path, user, remote_host, retry_on_refusal - 1, 
          connect_timeout = default_connection_timeout)

  # format the string
  out, err = deploy_logging.format_stdout_and_err(out, err)

  return out, err, returncode



def remote_upload_file(local_fn_path, user, remote_host, retry_on_refusal = 3, connect_timeout = default_connection_timeout):
  """
  <Purpose>
    This uses scp to upload a file to a remote computer.
     
  <Arguments>
    local_fn_path:
      Which file do we chuck to the remote computer?
    user:
      user to log in as
    remote_host:
      the ip/name of the machine we're connecting to.
    retry_on_refusal:
      Optional. Integer. Has number of times to retry the connection IF it was
      refused (built in to take care of not 'spamming' the remote server)
    connect_timeout:
      Optional. Integer. Time in seconds for ssh to timeout if no response was
      received.
    
  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    Tuple. (out, err, returncode)
    Details:
      out: stdout from scp
      err: err from ssh
      returncode: scp's exit code
  """

  # check that local file exists.
  if not os.path.isfile(local_fn_path):
    deploy_logging.logerror('Problem with local file: it does not exist!')
    raise Exception('Please check calling method.')
  
  scp_proc_handle = subprocess.Popen('scp -o BatchMode=yes -o '+\
      'ConnectTimeout='+str(connect_timeout)+' -o StrictHostKeyChecking=no '+\
      ' '+local_fn_path+' '+user+"@"+remote_host+":", shell = True, 
      stdout = subprocess.PIPE, stderr = subprocess.PIPE)

  scp_proc_pid = scp_proc_handle.pid

  # start thread to monitor timeouts (on another thread)
  deploy_threading.monitor_timeout(scp_proc_pid, int(connect_timeout), remote_host, user)

  # execute and block until done...
  out, err = scp_proc_handle.communicate('')

  returncode = scp_proc_handle.returncode

  # retry if conn. was refused?
  if retry_on_refusal:
    # check if we got a connection refused. if we did, could be cuz we're 
    # spamming the server, so sleep and then try again
    didwesleep = sleep_on_conn_refused(out, err, retry_on_refusal, remote_host)
    # we slept, so call function again and try to execute
    if didwesleep:
      # run again, but this time decrement retry counter
      out, err, returncode = remote_upload_file(local_fn_path, user, 
          remote_host, retry_on_refusal - 1, connect_timeout = default_connection_timeout)

  # format the string
  out, err = deploy_logging.format_stdout_and_err(out, err)

  return out, err, returncode

  
  
def sleep_on_conn_refused(out, err, timesleft, remote_host):
  """
  <Purpose>
    passed in stdout/stderr from ssh/scp, it checks if we had a refused 
    connection, and then returns true if we must retry it or not.
    
    Divides 60 seconds by how many times we have left to sleep.
    So if we retry 3 times...
      1st run: sleep 60/3 (20s)
      2nd run: sleep 60/2 (30s)
      3rd run: sleep 60/1 (60s)

    As you can see, the timeout increases.

  <Arguments>
    out:
      the stdout
    err:
      the stderr
    timesleft:
      how many times do we have left to try and connect.

  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    Boolean. True if we did a sleep, False if we didn't.
  """
  
  
  # checks if out/err have 'connection refused' string and waits to 
  # overcome timeout
  out_bool = out.lower().find('connection refused') > -1
  err_bool = err.lower().find('connection refused') > -1
  instructional_machine = '128.' in remote_host
  if instructional_machine:  
    if out_bool or err_bool:
      # sleep then try again
      deploy_logging.log('WARNING', "Connection refused, forced sleeping to overcome "+\
          "timeout ("+str(timesleft)+" timeouts left)")
      time.sleep(60/timesleft) # each time you sleep a little longer
      return True
  return False
