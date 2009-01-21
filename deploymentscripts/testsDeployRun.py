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
from subprocess import *

#further assumption is that scripts run in this order
slice="root"
expectedOutput='ProcessCheckerFinished\nfile_checker_finished'

commandLine='tar -xf stuff.tar; ./processCheckerFail.sh; ./fileChecker.sh;'

logfo=open('logs/'+strftime("%Y-%m-%d_%H.%M.%S"),'w');

#message for output and log
message=""

def copy_run(server):
  tempfilename = tempfile.mktemp()
  tempfilename = tempfilename.split('/')[-1]
  print tempfilename
  logtmp=open('logs/'+tempfilename,'w')#'+strftime("%Y-%m-%d_%H.%M.%S"),'w');
  m="\n----\nServer: "+server
  print m
  logtmp.write(m)
  
  server=server.strip()
  if os.system("scp -o StrictHostKeyChecking=no -o BatchMode=yes stuff.tar "+slice+"@"+server+":")!=0:
    m="scp failed for processChecker for "+server
    print m
    logtmp.write(m)
    exit(0)

  #open up a pipe for ssh communication
  p=Popen('ssh '+server,shell=True,stdout=PIPE,stdin=PIPE) 

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
    m="ERRORS in STDERR!\n"+stderr
    print m
    logtmp.write(m)

    
serverlist=[]
for server in file(sys.argv[1]):                                                                                                         
  serverlist.append(server.strip()) 

myutil.do_file(copy_run, serverlist, 20) 

#combine all of the files together
files = glob.glob('logs/tmp*')
for filename in files:
  file=open(filename,'r')
  content=file.read()
  file.close()
  logfo.write(content)

logfo.close()
#delete temporary files
for filename in files:
  os.remove(filename)
