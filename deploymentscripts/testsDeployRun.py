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
from subprocess import *

slice="root"
script1='processChecker.sh'
term1='ProcessCheckerFinished'

script2='fileChecker.sh'
term2='file_checker_finished'

for server in file(sys.argv[1]):

 server=server.strip()
 if os.system("scp -o StrictHostKeyChecking=no -o BatchMode=yes "+script1+" "+slice+"@"+server+":")!=0:
  print "scp failed for processChecker for "+server
 if os.system("scp -o StrictHostKeyChecking=no -o BatchMode=yes "+script2+" "+slice+"@"+server+":")!=0:
  print "scp failed for fileChecker for "+server

#open up a pipe for ssh communication
 p=Popen('ssh '+server,shell=True,stdout=PIPE,stdin=PIPE) 
 print "-----"

#execute scripts on the remote server
 (stdout, stderr)=p.communicate('./'+script1+';'+'./'+script2+';')#[0]

 print "Server: "+server

#indicate if script did not terminate properly

 if stdout.find(term1)<0:
   print "  PROCESS CHECKER DIDIN'T FINISH!"
# else: 
#  print "  PROCESS CHECKER FINISHED"

 if stdout.find(term2)<0:
   print "  FILE CHECKER DIDN'T FINISH!"
# else: 
#  print "  FILE CHECKER FINISHED"

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
  print "PROCESS CHECKER [FAILED]"
  print "FILE CHECKER [FAILED]"
 if passedScripts==1:
  print "PROCESS CHECKER [PASSED]"
  print "FILE CHECKER [FAILED]"
 if passedScripts==2:
  print "PROCESS CHECKER [FAILED]"
  print "FILE CHECKER [PASSED]"
 if passedScripts==3:
  print "FILE CHECKER [PASSED]"
  print "PROCESS CHECKER [PASSED]"

 if stderr:
  print "ERRORS in STDERR!"
  print stderr
