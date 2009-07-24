"""
<Program Name>
  deploy_logging.py

<Started>
  May 2009

<Author>
  n2k8000@u.washington.edu
  Konstantin Pik

<Purpose>
  This is the file contains logging-related functions that are used by the 
  deployment script.  This file is not to be executed by itself, but is to
  be used with other deploy_* modules.

<Usage>
  See deploy_main.py.
  
"""
import deploy_main
import make_summary
import thread
import os

# Lock on the log file - since we are going to launch multiple threads 
# that'll want to log things, we need to be careful. This lock should 
# take care of that.
filelock = thread.allocate_lock()

# So I don't have to type this out in the log file each time for a separator.
sep='------------------------------------------------------------------------'


def print_to_log(description_string, out, err, return_code):
  """
  <Purpose>
    helper that logs out, err, returncode to the proper files after formatting
    the output correctly.
    
  <Arguments>
    description_string:
      A description string to put in front of the stdout (e.g.: "Info")
    out: 
      stdout
    err:
      stderr
    return_code:
      the exit code of the call
    
    
  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    No returns.
  """
  
  out, err = format_stdout_and_err(out, err)
  
  if out:
    log(description_string, out+' (exit code'+str(return_code)+')')
  if err:
    logerror(err+' (exit code'+str(return_code)+')')

  

def format_stdout_and_err(out, err):
  """
  <Purpose>
    Helper that formats by removing trailing spaces and \n's, \t's, etc
     
  <Arguments>
    out: a string, stdout by convention
    err: a string, stderr by convection

    Note: can be any two strings.
    
  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    No returns.
  """
  
  out = out.strip('\n\t\r ')
  err = err.strip('\n\t\r ')
  return out, err

  
  
def logerror(data):
  """
  <Purpose>
    Wrapper to log to an error log file, and prints to console in case we're 
      running in near-silent mode (-v).
     
  <Arguments>
    The error description/etc.
    
  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    No returns.
  """
  
  # format data
  data = str(data)
  data = data.strip('\n ')
  data = data.replace('\n', ' | ')
  # don't want to OVERspam (this'll get printed if verbosity >=1)
  if deploy_main.verbosity < 1 :
    print 'ERROR:'+str(data)
  log('ERROR:', data, 'deploy.err')

  
  
  
# Controller = person running the tests
def log(identifier, data, fn='controller'):
  """
  <Purpose>
    Logs to <fn> the <data> with <host> as the identifier for that line
     
  <Arguments>
    identifier:
      identifier in front of the line. Used to show "where" an event happend
    data:
      the string to log to file
    fn:
      Optional. Default is controller (and .log is always added a fn). Where 
      the log file is.
    
  <Exceptions>
    Possible exception when can't open/write log file.

  <Side Effects>
    None.

  <Returns>
    No returns.
  """

  # multiple threads will try to write to this log file, gotta be careful
  filelock.acquire()

  try:
    # if for some reason the logging directory does not exist, then create it
    if not os.path.isdir('deploy.logs'):
      os.mkdir('deploy.logs')
    
    # logfile will be put in the local directory
    logfile = open('deploy.logs/'+fn+'.log', 'a')

    # format data
    data = str(data).strip('\n\r ')
    
    if data:
      # if we have an identifier thenlog it with the time
      if identifier:
        logfile.write('\n'+deploy_main.get_current_time()+" | "+str(identifier)+":  "+data) 
      else:
        # if it's empty then log just the data, no time or anything.
        # konp: FIXED 'no attribute err'
        logfile.write('\n'+data)

      # if verbose, print to console as well
      if deploy_main.verbosity > 0:
        print data

  except Exception, e:
    print "Error writing logfile ("+str(e)+")"
  finally:
    # close file and release lock
    logfile.close()
    filelock.release()


    
def build_summary():
  """
  <Purpose>
    This function collects all the important log files from the subdirectories
    and outputs them in a summary.log

  <Arguments>
    None.

  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    None.
  """

  # make a call to make_summary.py
  make_summary.build_summary()
