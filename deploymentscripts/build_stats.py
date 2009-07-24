"""
<Program Name>
  build_stats.py

<Started>
  June 2009

<Author>
  n2k8000@u.washington.edu
  Konstantin Pik

<Purpose>
  The purpose of this file is to generate stats from the files that have been
  gathered from various nodes by the deploy_* scripts.  This file does very 
  pretty simple string parsing in order to estimate stats, and as of right now
  is currently superceded by make_summary.py.  The only portions of this file that
  remain to be ported is the error grabbing code.


<Usage>

  python biuld_stats.py [timestamp]
  
  where [timestamp] is a unix time.  This'll tell the script which files to grab
  as the fileformat is [fn].timestamp (see main()) for more info)
  
"""

import subprocess
import sys
import os


# The master controller log file
controller_file = ''

# The error file to write later
err_file = ''

# The summary file to write later
summary_file = ''



def helper_uniq(log_data, as_string = True):
  """
  <Purpose>
    Helper that gets a bunch of lines from the log file, and then attemps to 
    count the unique hosts in those lines. Since failed hosts might have 
    several entries, we need to strip the date off first, and then count
    the unique entries (done via set).
    
  <Arguments>
    log_data:
      Data from the logs - could be one line, or multiple lines.
    as_string:
      Default value is True.
      True: return value as string
      False: return value as integer
    
  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    String/Integer. Returns the # of uniq lines (with the date stripped).
  """
  log_data_nodate = strip_date(log_data)
  # count the uniq lines in the output
  log_data_set = set(log_data_nodate.splitlines())
  if as_string:
    return str(len(log_data_set)) 
  else:
    return len(log_data_set)

    
    
def strip_date(log_data):
  """
  <Purpose>
    Strips the date from the line so that we can count the number of 'uniq'
    lines
    
    An input line would look something like this:
    Jun 19 2009 02:18:53 | ERROR::  planet6.berkeley.intel-research.net: Trouble uploading deploy.tar
    
    the returned value would be: 
    ERROR::  planet6.berkeley.intel-research.net: Trouble uploading deploy.tar
    
  <Arguments>
    log_data:
      Data from the logs - could be one line, or multiple lines.
    
  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    Returns log_data without the date
  """
  # we'll build up this string here.
  temp_to_return = []
  
  # for every line, find the | character and 
  for each_line in log_data.splitlines():
    # get index of the | bar
    bar_index = each_line.find('|')+1
    # get everything with to the right of the bar
    temp_to_return.append(each_line[bar_index:])
  return "\n".join(temp_to_return)

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
  

def get_uniq_machines():
  # find out how many machines total we surveyed
  # line looks like:
  # returns an (int, HumanString)
  # Jun 16 2009 01:56:07 | Setup:  Found 950 unique hosts to connect to.
  global controller_file
  out, err, retcode = shellexec("awk '/Found/ { print $8 } ' "+controller_file)
  try:
    out = out.strip('\n\r ')
    print out
    return (str(int(out)), 'There were '+out+' unique hosts surveyed\n\n')
  except ValueError, ve:
    print 'Unexpected number of uniq hosts returned from shell.'
    print ve
  except Exception, e:
    print 'Error in get_uniq_machines()'
    print e
 

def get_nodes_up():
    # returns (nodes_up, HumanString)
    # cheap way of seeing how many of the nodes our tests actually ran on..
    # sum up the "versions", which is a unique line per host-log.  This can be slightly
    # inaccurate
  out, err, retcode = shellexec('grep ^version '+summary_file+\
    ' | sort | uniq -c | awk \'{ print $1 }\'')
  # each line starts with a number, so convert to int and give it a try
  try:
    # this is how many computers are 'up'
    counter = 0
    for line in out.splitlines():
      counter += int(line)
  except ValueError, e:
    # ignore it, we don't really care
    pass
  except Exception, e:
    print 'Error in get_nodes_up'
    print e
  finally:
    return (counter, str(counter)+' hosts responded in a timely fashion '+\
      'and ran our tests.\n\n')
 
 
 
def get_nodes_by_version():
  # get the breakdown of hosts by version
  out, err, retcode = shellexec('grep ^version '+summary_file+' | sort | uniq -c')
  out_formatted = out.strip('\n\r ')
  
  # they keys are the versions, and they map to the number of that version currently running
  node_dict = {}
  return_string = "Breakdown of nodes by version:\n"+out+'\n'
  # sample string that we're going to process looks like this:
  # 2 version = "0.1e"
  # so first, let's split by lines
  out_array = out_formatted.splitlines()
  for each_line in out_array:
    if len(each_line.strip('\n\r ')) > 0:
      # not a blank line, so split by spaces and then we care about the first
      # and the last token (except we'll strip the double quotes off the last
      # token so that we have just the version number
      number_running = each_line.split(' ')[0]
      
      # this gives us ".01e", so let's now strip the quotes
      node_version = each_line.split(' ')[-1]
      node_version = each_line.strip('"')
      try:
        node_dict[node_version] = int(number_running)
      except ValueError, ve:
        print 'Invalid number of nodes, (NaN)'
        print ve
      except Exception, e:
        print 'Error in get_nodes_by_version()'
        print e
  return (out_array, return_string)


 
 
def get_unknown_files():
  out, err, retcode = shellexec("grep Unknown file "+summary_file+" | sort | uniq -c")    
  return_string = 'The following files are unrecognized and reside in the'+\
    ' seattle folder\n'
  # list of the files
  file_list = []
  if out.strip('\n\r '):
    return_string += out
    file_list = out.splitlines()
  else:
    return_string += '\tNone\n\n'
  return (file_list, return_string)

  
  
def get_num_python_errors():
  # check to see if there were any python errors
  out, err, retcode = shellexec("grep Traceback "+summary_file)
  return_string = "Number of python errors (see summary.log for "+\
    "additional details): "+str(len(out.splitlines()))+'\n'
  return (len(out.splitlines()), return_string)

  
  
def get_verifyprocess_summary():
  # get all the testprocess info and dump that as well
  out, err, retcode = shellexec("grep ^[[][^rI] "+summary_file+" | sort | uniq -c")
  return_string = 'The following information is reported by verifyprocess.py:\n'
  return_string += out+'\n'
  return return_string

  
  
def get_all_warnings():
  # now lets check for warnings from nodemanager and software manager logs
  out, err, retcode = shellexec("grep [[]WARN[]] "+summary_file+" | sort")
  return_string = 'Warnings gathered from SU and NM logs:\n'
  if out.strip('\n\r '):
    return_string += out
  else:
    return_string += '\tNone\n'
  return_string += '\n'
  return return_string
  
  
  
def get_all_errors():
  out, err, retcode = shellexec("grep '[[]ERROR[]]' "+summary_file+" | sort")
  return_string = 'Errors gathered from SU and NM logs:\n'
  if out.strip('\n\r '):
    return_string += out
  else:
    return_string += '\tNone\n'
  return_string += '\n'
  return return_string
  
  
  
def main():
  # sys.argv[1] holds the timestamp that we're intersted in.
  
  # by default it looks only ./detailed_logs directory, but otherwise it has 
  # special behavior and reprocesses old logs.
  
  global controller_file, err_file, summary_file
  try:
    timestamp = sys.argv[1]
    if not os.path.isdir('./detailed_logs'):
      print 'No files to look at! ./detailed_logs directory does not exist!'
      return
    file_handle = file('./detailed_logs/stats.'+timestamp, 'w')
  except Exception, e:
    print e
    return
  else:
    # sys.argv[1] holds the timestamp
    # the files we look at are
    # ./detailed_logs/controller.[timestamp]
    # ./detailed_logs/detailed.htmlsummary.[timestamp]
    # ./deploy.err.[timestamp]
    
    # got a summary file handle. lets now dump data there!
    controller_file = './detailed_logs/controller.'+timestamp
    err_file = './detailed_logs/deploy.err.'+timestamp
    summary_file = './detailed_logs/detailed.htmlsummary.'+timestamp
    
    # get the uniq machines list
    num_uniq_machines, human_string =  get_uniq_machines()
    file_handle.write(human_string)

    # get the number of nodes up
    num_nodes, human_string = get_nodes_up()
    file_handle.write(human_string)
    
    # get the version breakdown of the nodes
    version_dict, human_string = get_nodes_by_version()
    file_handle.write(human_string)
    file_handle.write(str(version_dict))
    
    # get a list of unknown files that reside in the directories
    file_list, human_string = get_unknown_files()
    file_handle.write(human_string)
    
    # get the number of python errors
    number_of_errors, human_string = get_num_python_errors()
    file_handle.write(human_string)

    # get the summary of the verifyprocess script
    summary_string = get_verifyprocess_summary()
    file_handle.write(summary_string)
    
    # get all the warnings from the v2 logs
    warning_strings = get_all_warnings()
    file_handle.write(warning_strings)

    # get all the errors from the v2 logs
    error_strings = get_all_errors()
    file_handle.write(error_strings)

    
    # find out all the machines that denied us entry and why
    # divided by some as that failure would cause the host to be put on the
    # 'retry' list of failed hosts, so we don't want to list duplicate hosts
    # how many rejected our key?
    out, err, retcode = shellexec("grep \"[^ ]Permission denied (\" "+err_file)
    out = out.strip('\n\r ')
    if out:
      uniq_hostnames = helper_uniq(out)
      file_handle.write('\nThere were '+uniq_hostnames+\
        ' machines who rejected our key')
    else:
      file_handle.write('\nAll computers accepted our key')
    file_handle.write('\n')
    
    # how many gave us a connection refused?
    out, err, retcode = shellexec("grep \"Connection refused\" "+err_file)
    out = out.strip('\n\r ')
    if out:
      uniq_hostnames = helper_uniq(out)
      file_handle.write('\nThere were '+uniq_hostnames+\
        ' machines who refused connection')
    else:
      file_handle.write('\nNo nodes gave us a connection refused error')
    file_handle.write('\n')

    # Connection timed out?
    out, err, retcode = shellexec("grep \"Connection timed out\" "+err_file)
    out = out.strip('\n\r ')
    if out:
      uniq_hostnames = helper_uniq(out)
      file_handle.write('\nThere were '+uniq_hostnames+\
        ' machines on which the connection timed out')
    else:
      file_handle.write('\nNo connections timed out.')
    file_handle.write('\n')

    # Name resolution error (temporary)?
    out, err, retcode = shellexec("grep \"Temporary failure in name resolution\" "+err_file)
    out = out.strip('\n\r ')
    if out:
      uniq_hostnames = helper_uniq(out)
      file_handle.write('\nThere were '+uniq_hostnames+\
        ' machines on which there was Temporary failure in name resolution')
    else:
      file_handle.write('\nNo temporary failures in name resolution.')
    file_handle.write('\n')

    # hostname could not be resolved?
    out, err, retcode = shellexec("grep \"Could not resolve hostname\" "+err_file)
    out = out.strip('\n\r ')
    if out:
      file_handle.write('\nThere were '+uniq_hostnames+\
        ' machines on which the hostname could not be resolved')
    else:
      file_handle.write('\nNo name resolution problems.')
    file_handle.write('\n')
    
    # counts the "WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED"
    out, err, retcode = shellexec("grep \"REMOTE HOST IDENTIFICATION HAS CHANGED\" "+err_file)
    out = out.strip('\n\r ')
    if out:
      uniq_hostnames = helper_uniq(out)
      file_handle.write('\nThere were '+uniq_hostnames+\
        ' machines that changed their key and ssh complained')
    else:
      pass
    file_handle.write('\n')    
    
    # this line makes a list of all of the machines that don't have seattle installed
    # sample line to be processed will look like this:
    # Jun 16 2009 09:16:18 | planetlab2.s3.kth.se: Error: Did not find any seattle installs on planetlab2.s3.kth.se. Aborting.(logdir: )
    out, err, retcode = shellexec("awk '/Did not/ { sub(\":\",\"\", $6); print $6 } ' "+summary_file)
    # each line has an IP, so lets count
    no_seattle = out.splitlines()
    file_handle.write('The following machines ('+str(len(no_seattle))+\
      ') do not have seattle installed:\n')
    if out.strip('\n\r '):
      file_handle.write('(also written to missing.list)\n')
      file_handle.write(out)
      try:
        missing_handle = file('missing.list.'+timestamp, 'w')
        missing_handle.write(out)
        missing_handle.close()
      except Exception, e:
        print "Trouble writing missing file's list"
    else:
      file_handle.write('\tNone\n')
    file_handle.write('\n')
    
    file_handle.write('End of log\n')
    file_handle.close()
    out, err, retcode = shellexec('cat ./detailed_logs/stats.'+timestamp)
    print out
    
if __name__ == "__main__":
  main()
