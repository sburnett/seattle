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
import tempfile
import glob
import threading
import datetime
import time
import signal

from time import strftime
#from subprocess import *
import subprocess

# use this instead:
#       import subprocess
# how you use it in the code:
#       subprocess.function()

#further assumption is that scripts run in this order
sliceLogin="uw_seattle"#"uw_seattle" #"root"
#expectedOutput='ProcessCheckerFinished\nfile_checker_finished'
expectedOutput='REACHED!\nfile_checker_finished\nProcessCheckerFinished\n'

#commandLine='tar -xf stuff.tar; ./processCheckerFail.sh; ./fileChecker.sh;'
commandLine='tar -xf testpack.tar; cd testpack; python verifyfiles.py -readfile verifyfiledict ~; python testprocess.py; exit;'



#message for output and log
message=""

def uploadTests(server):
  p1=subprocess.Popen('scp -o StrictHostKeyChecking=no -o BatchMode=yes testpack.tar '+sliceLogin+"@"+server+':',shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  start = datetime.datetime.now()
  timeout=700
  while p1.poll() is None:
      time.sleep(0.2)
      now=datetime.datetime.now()
      if (now-start).seconds > timeout:
          os.kill(p1.pid, signal.SIGKILL)
          os.waitpid(-1, os.WNOHANG)
          return None

  return p1

def runTests(server):
    #execute scripts on the remote server
#    commandLine='cd seattle_repy; ./start_seattle.sh; exit;'
    p=subprocess.Popen('echo "REACHED!"; ssh -o StrictHostKeyChecking=no -o BatchMode=yes '+sliceLogin+"@"+server,shell=True,stdout=subprocess.PIPE,stdin=subprocess.PIPE,stderr=subprocess.PIPE) 

    stdpair=p.communicate(commandLine)    #commandLine)#[0]
    start = datetime.datetime.now()
    timeout=500
    while p.poll() is None:
        time.sleep(0.2)
        now=datetime.datetime.now()
        if (now - start).seconds> timeout:
            os.kill(p.pid, signal.SIGKILL)
            os.waitpid(-1, os.WNOHANG)
            return None

#    os.waitpid(p.pid,0)

    return stdpair

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

  p1=None
  p1=uploadTests(server)

  #errors in stderr
  if p1 is not None and len(p1.stderr.read())>0:
    m="scp failed\n"
    logtmp.write(m)
  elif p1 is None:
    logtmp.write("Timeout on Scp")
    print "Scp Timeout"
  elif p1 is not None:

    stdpair=None
    stdpair=runTests(server)

    if stdpair is None:
       logtmp.write("Timeout on SSH")
       print "Timeout on SSH"
      
    elif stdpair is not None:
      (stdoutStr, stderrStr)=stdpair
 
      print "["+stdoutStr+"]"
      logtmp.write(stdoutStr)
  
      if stdoutStr!=expectedOutput:
        m="PROBLEM OCCURRED!\n"+"PO! "+server+"\n"

        logtmp.write(m)
      else:
        logtmp.write("GOOD!\n")

      if stderrStr:
        m="ERRORS in STDERR!\n"+stderrStr
        print m
        logtmp.write(m)


#execute provided function with items in the list as arguments (used by run_parallel)
def exec_list(which, func, list):
#  print "LIST CALLED: %d" % len(list)
  count=0
  for item in list:
    print "EXECUTING thread %d, item:%d of %d" % (which,count,len(list))
    count+=1
    func(item)

#runs provided function on the list of ip addresses in parallel (originally written by Justin Cappos)
def run_parallel(func, fulllist, forkthreads = 10):
  
  list = []
  for num in range(forkthreads):
    list.append([])

  thread = 0
  #distribute list of ip addresses to paralllizable slots
  for line in fulllist:
    list[thread%forkthreads].append(line.strip())
    thread = thread + 1
  
  for num in range(forkthreads):
    if os.fork()==0:
      if num<len(list):
        exec_list(num,func,list[num])
        os._exit(0)
  
  for num in range(forkthreads):
    if num<len(list):
      os.wait()


#check provided program aguments
def checkArgs(args):
  if len(args)!=2:
    return False
  if os.path.isdir(args[1]): 
    print "Must provide a file"
    return False


if __name__ == "__main__":
  
  if checkArgs(sys.argv)==False:
    print "Invalid arguments - usage: python testsDeployRun.py [iplist_file]"
    exit(0)



  # Reads the server list file specified in the command line 

  count=0
  serverlist=[]
  toadd=[]
  #put servers into several groups
  #to not start next group until previous finished
  for server in file(sys.argv[1]):                                          
    if (count==50):#number of nodes in a group
      serverlist.append(toadd)
      count=0
      toadd=[] 
    count+=1
    toadd.append(server.strip())

  serverlist.append(toadd)

  #deploy and run for each group
  for slist in serverlist:
    run_parallel(copy_run, slist, 20) 


  #combined logs file
  logfo=open('logs/'+strftime("%Y-%m-%d_%H.%M.%S"),'w');

  if (True):
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
