"""
<Program Name>
  None yet

<Started>
  January 18, 2009

<Author>
  Anthony Honstain

<Purpose>
  Measure the following resources
  resource cpu .50
  resource memory 20000000   # 20 Million bytes
  resource diskused 10000000 # 10 MB
  resource events 10
  resource filesopened 5

<TODO>
  How to handle failures in these methods they dont
  catch non-integer values from being returned, also different
  possible units on information in proc files?
"""

import commands
import sys

def parse_proc(keyword, file):
  """
  Instead of using re module or grep I do a parse of my own, probably
  not very roboust.  

  @param keyword: will search line by line for the keyword
  @param file: file name to search in  
  
  Should this method throw exception if bad file name?
  How should it indicate if the keyword was not found?
  Currently it uses a similar format to 
  commands.getstatusoutput() and returns a tuple is the
  first element being a linux exit value 0 or 1

  For now I will return a similar format to grep
  a tuple (exit code, line with information)
  since two different methods use this.
  """
  try:
    openfile = open(file, 'r') 
  except IOError:     
    #print 'Error: IOError bad file'
    return (1, '')

  #Read each line of the file and then compare each word in the line
  #to the desired string.
  for line in openfile:
    read_data = line.split()

    for word in read_data:
      if word == keyword:
        openfile.close()
        return (0, read_data)
  #print "Error: File not found."
  openfile.close()
  return (1, '')

def get_cpu():
  
  #Stores integer value for number of cores
  cpucores = ''
  
  #example value for searchresult: (0, ['cpu', 'cores',':', '2')  
  searchresult = parse_proc("cores", "/proc/cpuinfo")
       
  #This will catch a failed file-opening/parse
  if (searchresult[0] != 0):
	print 'Error: failed to find cpu core info'
	#TODO---
    #grep command failed to find cpu core info
    #THROW EXCEPTION OR RETURN DEFAULT?

  corestring = searchresult[1]
  cpucores = corestring[len(corestring)-1] 
    
  #TODO--- 
  #Needs to return appropriate float for percent of
  #cpu usage. NOT JUST THE NUMBER OF CORES. 
  #Should I catch a non-integer here?   
  return cpucores
  

def get_memory():
  """
  Anthony:
  Still not sure if proc allways stores in kB? Note that
  this affects which element of the list to take after parse.
  
  TODO - Need to test on machine with swap to ensure 
  swap is not counted.
  """

  #Stores an integer representing the number of free kB
  memory = 0
  
  #example value for searchresult: (0, ['MemTotal:', '2066344', 'kB'])  
  searchresult = parse_proc("MemTotal:", "/proc/meminfo")

  if (searchresult[0] != 0):
	return 20000000
    #TODO---
    #THROW EXCEPTION OR RETURN DEFAULT?
    
  memstring = searchresult[1]
  memory = memstring[len(memstring)-2]

  #Assuming memory will be stored in kB
  #memory is converted to bytes using 1kb = 10^3 bytes
  memory = int(memory) * (10**3) 
    
  #Note for later, kb string is stored if needed in memstring[len(memstring)-1]
  return memory


def get_diskused():
  """
  Returns the total size of the parition/mount that the
  working directory is on.
  """

  #Basic commands for linux stat
  # stat arguement -f get filesystem info
  # stat arguement -c use valid format sequence
  #   %s block size (faster transfer)
  #   %S Fundamental block size (for block count)
  #   %b Total data blocks in the file system.
  rawdatareturn = commands.getstatusoutput('stat -f  -c "%S %b" $PWD')
  
  #blocksize unit is bytes
  blocksize = 0
   
  freeblocks = 0
 
  # Test because if first element of tuple is other than 0
  # then the exit status of the linux command is an error.
  if (rawdatareturn[0] != 0):
    # Anthony Jan 19 2009:
    # TODO--- 
    # Returns the value from the restriction.txt file
    #print 'Error: stat command had error'
    #print rawdatareturn[1]
    return 10000000
    
  temp = (rawdatareturn[1]).split()
  blocksize = int(temp[0])
  freeblocks = int(temp[1])

  totalbytes = blocksize*freeblocks
  
  #Conversion made using 1MB = 10**6Bytes
  #totalmb = totalbytes / (10**6)
 
  return totalbytes 

def get_freediskspace():
  """
  NOTE: THIS RETURNS FREE DISK SPACE, different than get_diskused() 
  I guessed this might be usefull.   

  Will return the disk space available for non-super users
  in the working directory (integer/long number of bytes). 
  """
  # Basic commands for linux stat
  # stat arguement -f get filesystem info
  # stat arguement -c use valid format sequence
  #   %s block size (faster transfer)
  #   %S Fundamental block size (for block count)
  #   %a free blocks available to non-super user
  rawdatareturn = commands.getstatusoutput('stat -f  -c "%S %a" $PWD')
  
  #blocksize unit is bytes
  blocksize = 0
  
  #free blocks for non-super user  
  freeblocks = 0
 
  # Test because if first element of tuple is other than 0
  # then the exit status of the linux command is an error.
  if (rawdatareturn[0] != 0):
    # Anthony Jan 19 2009:
    # TODO--- 
    # Just returns default value from restrictions.txt
    #print 'Error: stat command had error'
    #print rawdatareturn[1]
    return 10000000
    
  temp = (rawdatareturn[1]).split()
  blocksize = int(temp[0])
  freeblocks = int(temp[1])

  totalbytes = blocksize*freeblocks
  
  #Conversion made using 1MB = 10**6Bytes
  #totalmb = totalbytes / (10**6)
 
  return totalbytes 


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
