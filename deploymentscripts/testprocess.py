"""
Author: Cosmin Barsan
The rawsay function and its dependencies have been written by Justin Cappos,
but the functions nmclient_rawcommunicate and nmclient_rawsay have been slightly modified to take ip and port arguments
instead of the original handle argument. This was done to keep the code simple and the file short.
The full functionality of signed requests is not needed for this test, since we are only using rawsay.

Motivation:
The purpose of this script is to be used as a component in an automated system that detects and fixes problems with the repy installation on linux machines. The purpose of this script is to detect problems with the node manager and software updater processes and report them. 

Description:
This script verifies whether the node manager process is running and verifies whether the software updater is running.
This script also verifies whether the ndoe manager si running on port 1224 by sending a getVessels request and waiting for a reply.
This script will only work on linux.
It is necessary that this script be run from a directory that contains the repyportability module and its dependencies. 

expected output:
ProcessCheckerFinished

If the software updater is not running the following is printed:
'[SoftwareUpdater] Software Updater is not running.'

If there are two or more Software Updater Processes running, the following is printed:
'[SoftwareUpdater] Multiple instances of Software Updater are running.'

If exactly one software updater process is running, but its memory usage is severely higher than expected, the following is printed:
[SoftwareUpdater] Software Updater memory usage is unussually high.

If exactly one software updater process is running, but its memory usage is severely lower than expected, the following is printed:
[SoftwareUpdater] Software Updater memory usage is unussually low.

If exactly one software updater process is running, but it is Stopped (T), Dead (X), or Defunct (Z), the following is printed:
[SoftwareUpdater] Software Updater process is Stopped, Dead, or Defunct.

If exactly one software updater process is running, but its cpu usage exceeds 50% the following is printed:
[SoftwareUpdater] Software Updater process has cpu usage above 50%.

If the node manager is not running, the following is printed:
'[NodeManager] Node Manager is not running.'

If there are two or more Node Manager Processes running, the following is printed:
'[NodeManager] Multiple instances of Node Manager are running.'

If exactly one node manager process is running, but its memory usage is severely higher than expected, the following is printed:
[NodeManager] Node Manager memory usage is unussually high.

If exactly one node manager process is running, but its memory usage is severely lower than expected, the following is printed:
[NodeManager] Node Manager memory usage is unussually low.

If exactly one node manager process is running, but it is Stopped (T), Dead (X), or Defunct (Z), the following is printed:
[NodeManager] Node Manager process is Stopped, Dead, or Defunct.

If exactly one node manager process is running, but its cpu usage exceeds 50% the following is printed:
[NodeManager] Node Manager process has cpu usage above 50%.

If the node manager is running, but is not responding to requests on port 1224, the following is printed:
'[NodeManager] Node Manager is not responding to requests on port 1224.'

Regardless of whether there are errors or not detected, ProcessCheckerFinished will be printed upon script termination.
"""

from repyportability import *
import subprocess #subprocess is used to check running processes

# Thrown when a failure occurs when trying to communicate with a node
class NMClientException(Exception):
  pass

class SessionEOF(Exception):
  pass

sessionmaxdigits = 20

def session_recvmessage(socketobj):

  messagesizestring = ''
  # first, read the number of characters...
  for junkcount in range(sessionmaxdigits):
    currentbyte = socketobj.recv(1)

    if currentbyte == '\n':
      break
    
    # not a valid digit
    if currentbyte not in '0123456789' and messagesizestring != '' and currentbyte != '-':
      raise ValueError, "Bad message size"
     
    messagesizestring = messagesizestring + currentbyte

  else:
    # too large
    raise ValueError, "Bad message size"

  messagesize = int(messagesizestring)
  
  # nothing to read...
  if messagesize == 0:
    return ''

  # end of messages
  if messagesize == -1:
    raise SessionEOF, "Connection Closed"

  if messagesize < 0:
    raise ValueError, "Bad message size"

  data = ''
  while len(data) < messagesize:
    chunk =  socketobj.recv(messagesize-len(data))
    if chunk == '': 
      raise SessionEOF, "Connection Closed"
    data = data + chunk

  return data
  
# a private helper function
def session_sendhelper(socketobj,data):
  sentlength = 0
  # if I'm still missing some, continue to send (I could have used sendall
  # instead but this isn't supported in repy currently)
  while sentlength < len(data):
    thissent = socketobj.send(data[sentlength:])
    sentlength = sentlength + thissent
    
# send the message 
def session_sendmessage(socketobj,data):
  header = str(len(data)) + '\n'
  session_sendhelper(socketobj,header)

  session_sendhelper(socketobj,data)
  

# Sends data to a node (opens the connection, writes the 
# communication header, sends all the data, receives the result, and returns
# the result)...
def nmclient_rawcommunicate(nmip, nmport, *args):

  try:
    thisconnobject = openconn(nmip, nmport) 
  except Exception, e:
    raise NMClientException, str(e)

  # always close the connobject
  try:

    # send the args separated by '|' chars (as is expected by the node manager)
    session_sendmessage(thisconnobject, '|'.join(args))
    return session_recvmessage(thisconnobject)
  except Exception, e:
    raise NMClientException, str(e)
  finally:
    thisconnobject.close()


# Public:  Use this for non-signed operations...
def nmclient_rawsay(nmip, nmport, *args):
  fullresponse = nmclient_rawcommunicate(nmip, nmport, *args)

  try:
    (response, status) = fullresponse.rsplit('\n',1)
  except KeyError:
    raise NMClientException, "Communication error '"+fullresponse+"'"

  if status == 'Success':
    return response
  elif status == 'Error':
    raise NMClientException, "Node Manager error '"+response+"'"
  elif status == 'Warning':
    raise NMClientException, "Node Manager warning '"+response+"'"
  else:
    raise NMClientException, "Unknown status '"+fullresponse+"'"


####SOFTWARE UPDATER TESTS####

#check if there is a software updater running
ps = subprocess.Popen('ps -ef | grep "python softwareupdater.py" | grep -v grep', shell=True, stdout=subprocess.PIPE) 
updater_out = ps.stdout.read()

if(updater_out == ""):
  print "[SoftwareUpdater] Software Updater is not running."



#check if there are multiple software updater processes running 
updater_num = len(updater_out.splitlines())
if (updater_num >1):
  print "[SoftwareUpdater] Multiple instances of Software Updater are running."



#check the memory usage of the software updater process. We only do this if there is a single instance of
#software updater running.
if (updater_num == 1):
  #first get the process id from the output
  updater_pid = (updater_out.split())[1]
  
  #get the memory usage for the process
  for count in range(1,10):
    # JAC: I've changed this from 'size' to 'rss' because this is more accurate
    # for systems that don't have memory paged out (see: #468)
    ps = subprocess.Popen('ps o pid,rss ' + str(updater_pid) + ' | grep -v PID', shell=True, stdout=subprocess.PIPE)
    rawstring = ps.stdout.read()
    #make sure we have at least two lines of output
    if len(rawstring)>=2:
      break
      
  if len(rawstring)<2:
    raise Exception, "unexpected output from ps:" + str(rawstring)
  
  updater_mem = (rawstring.split())[1]

  #check if the memory usage (in KB) is too large or to small, typical usage is about 4500KB
  if (int(updater_mem) > 9000):
    print "[SoftwareUpdater] Software Updater memory usage is unusually high."
    print "[SoftwareUpdater] Software Updater memory usage is ("+str(updater_mem)+")"
  elif (int(updater_mem) < 2000):
    print "[SoftwareUpdater] Software Updater memory usage is unusually low."



#check the state of the software updater process. We only do this if there is a single instance of
#software updater running.
if (updater_num == 1):
  #first get the process id from the output
  updater_pid = (updater_out.split())[1]
  
  #get the state code for the process
  for count in range(1,10):
    ps = subprocess.Popen('ps o pid,stat ' + str(updater_pid) + ' | grep -v PID', shell=True, stdout=subprocess.PIPE)
    rawstring = ps.stdout.read()
  
    #make sure we have at least two lines of output
    if len(rawstring)>=2:
      break
      
  if len(rawstring)<2:
    raise Exception, "unexpected output from ps:" + str(rawstring)
    
  rawcode = (rawstring.split())[1]

  #we only care about the first character in the status code
  updater_stat = rawcode[0]

  #check if the state is Stopped (T), Dead (X), or Defunct (Z)
  # CNB: I changed the third test from 'updater_stat == "T"' - 
  # I'm assuming this was a typo
  if (updater_stat == "T" or updater_stat == "X" or updater_stat == "Z"):
    print "[SoftwareUpdater] Software Updater process is Stopped, Dead, or Defunct."



#check the cpu ussage of the software updater. We only do this if there is a single instance of
#software updater running.
if (updater_num == 1):
  #first get the process id from the output
  updater_pid = (updater_out.split())[1]
  
  #get the cpu usage for the process
  for count in range(1,10):
  
    ps = subprocess.Popen('ps o pid,cp ' + str(updater_pid) + ' | grep -v PID', shell=True, stdout=subprocess.PIPE)
    rawstring = ps.stdout.read()
    
    #make sure we have at least two lines of output
    if len(rawstring)>=2:
      break
      
  if len(rawstring)<2:
    raise Exception, "unexpected output from ps:" + str(rawstring)
    
  updater_cpu = (rawstring.split())[1]

  #check if the cpu usage exceeds 50% (if cp value is above 500)
  if (int(updater_cpu) > 500):
    print "[SoftwareUpdater] Software Updater process has cpu usage above 50%."



####NODE MANAGER TESTS####

#check if there is an instance of the node manager running
ps = subprocess.Popen('ps -ef | grep "python nmmain.py" | grep -v grep', shell=True, stdout=subprocess.PIPE) 
nm_out = ps.stdout.read()

if(nm_out == ""):
  print "[NodeManager] Node Manager is not running."



#check if there are multiple node manager processes running 
nm_num = len(nm_out.splitlines())
if (nm_num >1):
  print "[NodeManager] Multiple instances of Node Manager are running."



#check the memory usage of the software updater process. We only do this if there is a single instance of
#software updater running.
if (nm_num == 1):
  #first get the process id from the output
  nm_pid = (nm_out.split())[1]
  
  #get the memory usage for the process
  for count in range(1,10):
    ps = subprocess.Popen('ps o pid,size ' + str(nm_pid) + ' | grep -v PID', shell=True, stdout=subprocess.PIPE)
    rawstring = ps.stdout.read()
    
    #make sure we have at least two lines of output
    if len(rawstring)>=2:
      break
      
  if len(rawstring)<2:
    raise Exception, "unexpected output from ps:" + str(rawstring)
    
  nm_mem = (rawstring.split())[1]

  #check if the memory usage (in KB) is too large or to small, typical usage is about 70000KB
  if (int(nm_mem) > 130000):
    print "[NodeManager] Node Manager memory usage is unusually high."
  elif (int(nm_mem) < 20000):
    print "[NodeManager] Node Manager memory usage is unusually low."



#check the state of the node manager process. We only do this if there is a single instance of
#node manager running.
if (nm_num == 1):
  #first get the process id from the output
  nm_pid = (nm_out.split())[1]
  
  #get the state code for the process
  for count in range(1,10):
    ps = subprocess.Popen('ps o pid,stat ' + str(nm_pid) + ' | grep -v PID', shell=True, stdout=subprocess.PIPE)
    rawstring = ps.stdout.read()
    
    #make sure we have at least two lines of output
    if len(rawstring)>=2:
      break
      
  if len(rawstring)<2:
    raise Exception, "unexpected output from ps:" + str(rawstring)
    
  rawcode = (rawstring.split())[1]

  #we only care about the first character in the status code
  nm_stat = rawcode[0]

  #check if the state is Stopped (T), Dead (X), or Defunct (Z)
  # CNB: See my earlier edit, I think the original double 
  # 'nm_stat == "T"' was a typo.
  if (nm_stat == "T" or nm_stat == "X" or nm_stat == "Z"):
    print "[NodeManager] Node Manager process is Stopped, Dead, or Defunct."



#check the cpu ussage of the node manager. We only do this if there is a single instance of
#node manager running.
if (nm_num == 1):
  #first get the process id from the output
  nm_pid = (nm_out.split())[1]
  
  #get the cpu usage for the process
  for count in range(1,10):
    ps = subprocess.Popen('ps o pid,cp ' + str(nm_pid) + ' | grep -v PID', shell=True, stdout=subprocess.PIPE)
    rawstring = ps.stdout.read()

    #make sure we have at least two lines of output
    if len(rawstring)>=2:
      break
      
  if len(rawstring)<2:
    raise Exception, "unexpected output from ps:" + str(rawstring)
    
  nm_cpu = (rawstring.split())[1]

  #check if the cpu usage exceeds 50% (if cp value is above 500)
  if (int(nm_cpu) > 500):
    print "[NodeManager] Node Manager process has cpu usage above 50%."



#this is the section where we send a request to the node manager on port 1224 and see it if responds
#we only want to do this in the case there is at least one instance of the node manager running
if(nm_out != ""):

  #try to send the request and log if there is a failure
  try:
    nmclient_rawsay(getmyip(), 1224, "GetVessels")
    
  except NMClientException, e:
    #in the event of an exception, log the problem"
    print "[NodeManager] When contacting the Node Manager, received error '"+str(e)+"'"
    
#print ProcessCheckerFinished regardless of whether there were any failures.
print "ProcessCheckerFinished"
