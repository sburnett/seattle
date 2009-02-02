"""
<Program Name>
  None yet

<Started>
  January 18, 2009

<Author>
  Anthony Honstain

<Purpose>
  Measure system resources on a Linux system, makes
  extensive use of /proc files 

<TODO>
  How to handle failures in these methods they dont
  catch non-integer values from being returned, also different
  possible units on information in proc files?
"""

import commands
import sys

def get_cpu():
  
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

  disksize = 0
  disksizedefault = 10000000
 
  #blocksize unit is bytes
  blocksize = 0
  freeblocks = 0

  #Basic commands for linux stat
  # stat arguement -f get filesystem info
  # stat arguement -c use valid format sequence
  #   %s block size (faster transfer)
  #   %S Fundamental block size (for block count)
  #   %b Total data blocks in the file system.
  statresult = commands.getstatusoutput('stat -f  -c "%S %b" $PWD')
   
  # Test because if first element of tuple is other than 0
  # then the exit status of the linux command is an error.
  if (statresult[0] != 0):
    #Failed
    return disksizedefault
    
  statresult = (statresult[1]).split()
  #Example of expected value for statresult
  #['4096', '3751807']

  try:
    blocksize = long(statresult[0])
  except ValueError:
    return disksizedefault

  try:
    freeblocks = long(statresult[1])
  except ValueError:
    return disksizedefault

  disksize = blocksize * freeblocks 
  return disksize 


def get_freediskspace():
  """
  NOTE: THIS RETURNS FREE DISK SPACE, different than get_diskused() 
  I guessed this might be usefull.   

  Will return the disk space available for non-super users
  in the working directory (integer/long number of bytes). 
 
  """

  disksize = 0
  disksizedefault = 10000000
 
  #blocksize unit is bytes
  blocksize = 0
  freeblocks = 0

  #Basic commands for linux stat
  # stat arguement -f get filesystem info
  # stat arguement -c use valid format sequence
  #   %s block size (faster transfer)
  #   %S Fundamental block size (for block count)
  #   %a free blocks available to non-super user
  statresult = commands.getstatusoutput('stat -f  -c "%S %a" $PWD')
   
  # Test because if first element of tuple is other than 0
  # then the exit status of the linux command is an error.
  if (statresult[0] != 0):
    #Failed
    return disksizedefault
    
  statresult = (statresult[1]).split()
  #Example of expected value for statresult
  #['4096', '3751807']

  try:
    blocksize = long(statresult[0])
  except ValueError:
    return disksizedefault

  try:
    freeblocks = long(statresult[1])
  except ValueError:
    return disksizedefault

  disksize = blocksize * freeblocks 
  return disksize 


def get_events():
  maxevents = 0
  
  try:
    openfile = open('/proc/sys/kernel/threads-max', 'r') 
  except IOError:     
    return 10
  
  #TODO---
  #Should I catch the file read to make sure its an int?
  maxevents = int(openfile.read()) 
  openfile.close()
    
  return maxevents


def get_filesopened():
  maxfile = 0
  
  try:
    openfile = open('/proc/sys/fs/file-max', 'r') 
  except IOError:     
    return 5
  
  #TODO---
  #Should I catch file read to make sure its an int?
  maxfile = int(openfile.read()) 
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
