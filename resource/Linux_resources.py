"""
<Program Name>
  Linux_resources.py

<Started>
  January 18, 2009

<Author>
  Anthony Honstain

<Purpose>
  Measure system resources on a Linux system, makes
  extensive use of /proc files and df command for
  disk info.

  
"""

import commands
import sys

def get_cpu():
  """
  Anthony - still has difficulty sorting out difference
  between hyperthreading, multi-core, multi-processor.
  """
  #Stores integer value for number of cores
  cpucores = ''
  cpudefault = 1

  try:
    openfile = open("/proc/cpuinfo", 'r') 
  except IOError:     
    return cpudefault

  #Read each line of the file and then compare 
  #each word in the line to the desired string.
  for line in openfile:
    splitline = line.split()

    for word in splitline:
      #example value for desired read_data
      #['cpu', 'cores',':', '2'] 
      if word == "cores":
        cpucores = splitline[3]
        openfile.close()       
        try:
          return int(cpucores)
        except ValueError:
          return cpudefault

  openfile.close()
  return cpudefault  
  

def get_memory():
  """
  Anthony:
  Still not sure if proc allways stores in kB? Note that
  this affects which element of the list to take after parse.
  
  TODO - Need to test on machine with swap to ensure 
  swap is not counted.
  """

  memory = ''
  memorydefault = 20000000
  
  try:
    openfile = open("/proc/meminfo", 'r') 
  except IOError:     
    return memorydefault

  #Read each line of the file and then compare 
  #each word in the line to the desired string.
  for line in openfile:
    splitline = line.split()

    for word in splitline:
      #example value for desired splitline
      #['MemTotal:', '2066344', 'kB']
      if word == "MemTotal:":
        memory = splitline[1]
        openfile.close()  
     
        try:
          memory = long(memory)
        except ValueError:
          return memorydefault
        #Assuming memory will be stored in kB
        #memory is converted to bytes using 1kb = 10^3 bytes
        memory = memory * (10**3) 
        return memory  
  
  openfile.close()
  return memorydefault


def get_diskused():
  """
  Returns the total size in Bytes of the parition/mount that the
  working directory is on.
  """

  disksizedefault = 10000000
 
  #blocks are typically 1024bytes
  blocksize = 1024
  freeblocks = 0

  #Unix command df
  #-P, --portability     use the POSIX output format
  #Possible result from "df -P ."
  # Filesystem  1024-blocks  Used  Available Capacity Mounted on
  # /dev/sda1   15007228   5645076  8757148      40%    /
  statresult = commands.getstatusoutput('df -P .')
   
  # Test because if first element of tuple is other than 0
  # then the exit status of the linux command is an error.
  if (statresult[0] != 0):
    return disksizedefault
  
  # Second element of tuple returned by commands.getstatusoutput
  # is the stdout from the command.  
  statresult = (statresult[1]).split()

  try:
    freeblocks = long(statresult[10])
  except ValueError:
    return disksizedefault

  disksize = blocksize * freeblocks 
  return disksize 


def get_events():
  maxevents = 0
  defaultevents = 10  

  try:
    openfile = open('/proc/sys/kernel/threads-max', 'r') 
  except IOError:     
    return defaultevents
  
  try:
    maxevents = int(openfile.read())
  except ValueError:
    openfile.close()
    return defaultevents 
   
  openfile.close()
  return maxevents


def get_filesopened():
  """
  Reads the value stored in /proc/sys/fs/file-max
  May not represent the number of file descriptors
  that a user/process is able to obtain.
  """
  maxfile = 0
  defaultmaxfile = 5  

  try:
    openfile = open('/proc/sys/fs/file-max', 'r') 
  except IOError:     
    return defaultmaxfile
  
  try:
    maxfile = int(openfile.read())
  except ValueError:
    openfile.close()
    return defaultmaxfile

  openfile.close()
  return maxfile


"""
  Measure the following resources
  resource cpu .50
  resource memory 20000000   # 20 Million bytes
  resource diskused 10000000 # 10 MB
  resource events 10
  resource filewrite 10000
  resource fileread 10000
  resource filesopened 5
"""

print 'resource cpu', get_cpu()
print 'resource memory', get_memory()
print 'resource diskused', get_diskused()
print 'resource events', get_events()
print 'resource filesopened', get_filesopened()
