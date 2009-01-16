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

#Popen("ssh -t -t 192.168.0.22",shell=True,stdin=PIPE)#,stdout=PIPE)
#p=Popen('ssh -t -t 192.168.0.22',shell=True,stdin=PIPE,stdout=PIPE)#,shell=True,stdin=PIPE)#,stdout=PIPE)
#p.stdin.write('ls');
#print p.stdout;


slice="root"
for server in file(sys.argv[1]):

 server=server.strip()#"192.168.0.22"
 if os.system("scp -o StrictHostKeyChecking=no -o BatchMode=yes processChecker.sh "+slice+"@"+server+":")!=0:
  print "scp failed for processChecker for "+server
 if os.system("scp -o StrictHostKeyChecking=no -o BatchMode=yes fileChecker.sh "+slice+"@"+server+":")!=0:
  print "scp failed for fileChecker for "+server

# if True:

# print server.strip()
# p=Popen('scp -o StrictHostKeyChecking=no -o BatchMode=yes iplist root@'+server+':',shell=True,stdout=PIPE,stdin=PIPE)
# p=Popen('scp -o StrictHostKeyChecking=no -o BatchMode=yes iplist root@'+server+':',shell=True,stdout=PIPE,stdin=PIPE)
 p=Popen('ssh '+server,shell=True,stdout=PIPE,stdin=PIPE) 
#    print "scp failed for "+server
 #   return
 #(s,e)=p.communicate('ssh root@'+server.strip());
# (s,e)=p.communicate('ls');
 #p.communicate('exit');
 #print s
 print "-----"

 #serverlist.append(server.strip());

#(stdoutu, stderru)=p.communicate('./test.sh')#[0]
#p=Popen('./test.sh',shell=True,stdout=PIPE,stdin=PIPE)
 (stdout, stderr)=p.communicate('./processChecker.sh;./fileChecker.sh;')#[0]
#repr(stdout)
#print stdoutu

#(stdout, stderr)=p.communicate('./test.sh')#[0]
#print stdout
 print "Server: "+server
 if stdout.find("file_checker_finished")>=0:
  print "  FILE CHECKER PASS"
 else: 
  print "  FILE CHECKER ERROR"

 if stdout.find("ProcessCheckerFinished")>=0:
  print "  PROCESS CHECKER PASS"
 else: 
  print "  PROCESS CHECKER ERROR"


#p.communicate('exit')
#print "EXITED"

#print stdout
#for line in p.readlines():
 #   print line#+"oeuoeu"
#p=Popen('ls',shell=True,stdout=PIPE,stdin=PIPE)
#print >>output, "ls"
#print >>output, "exit"
#print p.stdout

#print output



#o=p.communicate()
#p.stdin.write("TEST")
#p.stdin.write("exit")
#o.write("TEST");
#print 'ls %s' % o[1]
#p.write("ls");
#print out;
#p=os.popen('ssh 192.168.0.22',"rw")
#p.write('./test.sh')
#p.close()

#p=os.popen('ls',"w")
#prii.read();
#for line in p.readlines():
 #   print line+"oeuoeu"
#  if line=="[FAILED]":
    


#print i.read()
#p.write('exit')

#p=os.popen('ssh 192.168.0.22',"w")
#p.write('ls')

#print p.read()
#p.write('ping 192.168.0.10');
#p.write('exit')
#print "HERE I AM";
#print "Content-type: text/html\n\n"
#print sys.platform[:5]

#print "hello world";
