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
from time import strftime
from subprocess import *

#further assumption is that scripts run in this order
slice="root"
script1='processChecker.sh'
term1='ProcessCheckerFinished'

script2='fileChecker.sh'
term2='file_checker_finished'

log=open('logs/'+strftime("%Y-%m-%d_%H:%M:%S"),'w');
#message for output and log
message=""

for server in file(sys.argv[1]):

 m="\n----\nServer: "+server
 print m; log.write(m)

 server=server.strip()
 if os.system("scp -o StrictHostKeyChecking=no -o BatchMode=yes "+script1+" "+slice+"@"+server+":")!=0:
  m="scp failed for processChecker for "+server
  print m;log.write(m)

 if os.system("scp -o StrictHostKeyChecking=no -o BatchMode=yes "+script2+" "+slice+"@"+server+":")!=0:
  m="scp failed for fileChecker for "+server
  print m; log.write(m)

#open up a pipe for ssh communication
 p=Popen('ssh '+server,shell=True,stdout=PIPE,stdin=PIPE) 

#execute scripts on the remote server
 (stdout, stderr)=p.communicate('./'+script1+';'+'./'+script2+';')#[0]
 

#indicate if script did not terminate properly

 if stdout.find(term1)<0:
   m="  PROCESS CHECKER DIDIN'T FINISH!"
# else: 
#  m="  PROCESS CHECKER FINISHED"
   print m; log.write(m)

 if stdout.find(term2)<0:
   m="  FILE CHECKER DIDN'T FINISH!"
# else: 
#  m="  FILE CHECKER FINISHED"
   print m; log.write(m)

#split the output into an array
 output=stdout.split('\n');

#indicates which scripts have passed 1=only first, 2=only second, 3=first and second etc.
 passedScripts=0


#line of output at which script ends
 line=0
#these are a rough check if there are any problems(from the output)
#need to rewrite this to use nicer math
 for i in range (0,len(output)):
  if output[i].find(term1)>=0:
   line=i
   if i==0:
    passedScripts=1
  if output[i].find(term2)>=0:
   if i-line==1:
    passedScripts+=2

 if passedScripts==0:
  m="PROCESS CHECKER [FAILED]\nFILE CHECKER [FAILED]"
 if passedScripts==1:
  m="PROCESS CHECKER [PASSED]\nFILE CHECKER [FAILED]"
 if passedScripts==2:
  m="PROCESS CHECKER [FAILED]\nFILE CHECKER [PASSED]"
 if passedScripts==3:
  m="FILE CHECKER [PASSED]\nPROCESS CHECKER [PASSED]"

 print m; log.write(m)

 if stderr:
  m="ERRORS in STDERR!\n"+stderr
  print m; log.write(m)
