#!/usr/bin/python
"""
<Program Name>
testsDeployRun.py

<Started>
Jan, 2008

<Author>
sal@cs.washington.edu
Salikh Bagaveyev

<Purpose>
Deploy and run tests. Report summary.

<Usage>
provide a file with a list of servers as an argument
"""

import os
import sys
import myutil
import tempfile
import glob

from time import strftime
#from subprocess import *
import subprocess

# use this instead:
#       import subprocess
# how you use it in the code:
#       subprocess.function()

#further assumption is that scripts run in this order
sliceLogin="root"
expectedOutput='ProcessCheckerFinished\nfile_checker_finished'

commandLine='tar -xf stuff.tar; ./processCheckerFail.sh; ./fileChecker.sh;'


#message for output and log
message=""

def copy_run(server):
  """
  <Purpose>
    Run test scripts on the remote computer by copying a file to the
    node (using scp) specified by argument "server", execute the test on that
    server capture output into the temporary log files. Then it
    reports if the execution was a success or a failure.

  <Arguments>
    server:
       A node IP/hostname to/at which upload/execute script/commands

  <Exceptions>
    None   

  <Side Effects>
    Creates local log files with remote execution output. Uploads files to remote computer using scp
    and executes them there.

  <Returns>
    None.
  """



  tempfilename = tempfile.mktemp()
  tempfilename = tempfilename.split('/')[-1]
  print tempfilename
  logtmp=open('logs/'+tempfilename,'w')#'+strftime("%Y-%m-%d_%H.%M.%S"),'w');
  m = '\n\n' + '-' * 50 + '\n'
  m += "Testing on node: " + server + "\n"
  m += '-' * 50 + '\n'
  print m
  logtmp.write(m)
  
  server=server.strip()
  if os.system("scp -o StrictHostKeyChecking=no -o BatchMode=yes stuff.tar "+sliceLogin+"@"+server+":")!=0:
    m="scp failed for processChecker for "+server
    print m
    logtmp.write(m)
    exit(0)

  #open up a pipe for ssh communication
  p=subprocess.Popen('ssh '+server,shell=True,stdout=subprocess.PIPE,stdin=subprocess.PIPE) 

  #execute scripts on the remote server
  (stdoutStr, stderrStr)=p.communicate(commandLine)    #commandLine)#[0]
  print stdoutStr 
  #indicate if script did not terminate properly

  print stdoutStr
  logtmp.write(stdoutStr)
  
  if stdoutStr!=expectedOutput:
    m="PROBLEM OCCURRED!"
    print m
    logtmp.write(m)

  if stderrStr:
    m="ERRORS in STDERR!\n"+stderrStr
    print m
    logtmp.write(m)




if __name__ == "__main__":
  logfo=open('logs/'+strftime("%Y-%m-%d_%H.%M.%S"),'w');

  # Reads the server list file specified in the command line 
  serverlist=[]
  for server in file(sys.argv[1]):                                                                                                         
    serverlist.append(server.strip()) 

  myutil.do_file(copy_run, serverlist, 20) 

  #combine all of the files together
  files = glob.glob('logs/tmp*')
  for filename in files:
    tmplog_file=open(filename,'r')
    content=tmplog_file.read()
    tmplog_file.close()
    logfo.write(content)

  logfo.close()
  #delete temporary files
  for filename in files:
    os.remove(filename)
