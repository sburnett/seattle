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
  
<Notes about cpu measurement>
  Two different ways to measure the number of processors is offered.
  
  get_cpu() will return the number of physical processors/cores that
  are on the machine. There is no strait forward way to directly measure
  this as a computer could have multiple processors with multiple cores
  and possibly be hyperthreaded as well.
  
  get_cpu_virtual() will return the total number processors (both virtual
  and physical) as would be the case on a processors with hyperthreading.
  
  Test cases and reasoning behind get_cpu()

  EXAMPLE 1) Core2Duo dual core no HT
    $ grep 'processors' /proc/cpuinfo
    processor    : 0
    processor    : 1
    $ grep 'cores' /proc/cpuinfo
    cpu cores    : 2
    cpu cores    : 2
    $ grep 'physical' /proc/cpuinfo
    physical id    : 0
    physical id    : 0
    
    Result: Multiple cores on a single chip will have the same physical
    id and each processors will list its number of cores.

  EXAMPLE 2) ATTU's dual core xenon with HT
    attu3 ~]$  grep 'processor' /proc/cpuinfo
    processor    : 0
    processor    : 1
    processor    : 2
    processor    : 3
    attu3 ~]$ grep 'cores' /proc/cpuinfo
    cpu cores    : 1
    cpu cores    : 1
    cpu cores    : 1
    cpu cores    : 1
    attu3 ~]$ grep 'physical' /proc/cpuinfo
    physical id    : 0
    physical id    : 3
    physical id    : 0
    physical id    : 3
    
    Results: Two physical processors with one core each, but have 
    hyperthreading enabled. 

  EXAMPLE 3) Pentium 3 with HT
    grep 'processor' /proc/cpuinfo
    processor    :0
    processor    :1
    grep 'cores' /proc/cpuinfo
    cpu cores     :1
    cpu cores     :1
    grep 'physical' /proc/cpuinfo
    physical id    :0
    physical id    :0
    
  OVERALL RESULTS: Judging from examples 1-3, if the number of physical id's
  is multiplied by the number of cores we arrive at the correct number
  of processors on the computer.     
"""

import commands

def count_Processor(procfile):
  """
  <Purpose>
    count_Processor will return the number of physical and virtual 
    processors that are recorded in the /proc/cpuinfo file.
    
    Each processor (both physical and virtual) will have its statistics
    recorded in the /proc/cpuinfo file.
    Example
 
    processor  : 0
    vendor_id  : GenuineIntel
    ...

    processor  : 1
    ...
    The count of processors is done by counting the number of lines
    that contain the word processor.

  <Arguments>
    procfile:
           A list with each line from the /proc/cpuinfo as an element.
           
  <Exceptions>
    Exception raised if no lines in /proc/cpuinfo contain the
    string processor.
    
  <Returns>
    The total number of virtual and physical processors.
  """
  count = 0
  # Read each line of the file and look for lines containing "processor"
  for line in procfile:
    if (line.find("processor") != -1):
      count += 1
  if(count > 0):
    return count
  else:
    raise Exception('processor data not found')


def count_Cores(procfile):
  """
  <Purpose>
    count_Cores will return the number of cpu cores that are 
    recorded by the processor in the /proc/cpuinfo file.
    HELPER FUNCTION FOR get_cpu()
    
  <Arguments>
    procfile:
           A list with each line from the /proc/cpuinfo as an element.
           
  <Exceptions>
    ValueError if invalid element for the number of cores.
    Exception raised if no lines in /proc/cpuinfo contain the
    string 'cpu cores'.
    
  <Returns>
    The total number of cores for a single physical processor.
  """
  # Search each line for the desired string
  for line in procfile:
    if (line.find("cpu cores") != -1):
      splitline = line.split()
      # example value for desired line from /proc/cpuinfo
      # ['cpu', 'cores',':', '2'] 
      cpucores = splitline[-1]      
      try:
        return int(cpucores)
      except ValueError:
        raise
  raise Exception('cpu cores data not found')
    
def count_ProcessorPhysicalId(procfile):
  """
  <Purpose>
    count_ProcessorPhysicalId will search each line of a the
    /proc/cpuinfo file and record each unique physical id and
    return the total number of unique id's.
    HELPER FUNCTION FOR get_cpu()
    
  <Arguments>
    procfile:
           A list with each line from the /proc/cpuinfo as an element.
           
  <Exceptions>
    ValueError is the physical id was not an integer.
    Exception raised if no lines in /proc/cpuinfo contain the
    contained information on the 'physical id'.
    
  <Returns>
    The total number unique identifiers.
  """
  id_list = []
  for line in procfile:
    if (line.find("physical id") != -1):
      splitline = line.split()
      # example value for desired line from /proc/cpuinfo
      # ['physical', 'id',':', '3'] 
      phys_id = splitline[-1]      
      try:
        phys_id = int(phys_id)
      except ValueError:
        raise
      if(phys_id not in id_list):
        id_list.append(phys_id)
  
  if(len(id_list) > 0):
    return len(id_list) 
  else:      
    raise Exception('physical id data not found')
 
def get_cpu():
  """
  <Purpose>
    Measure the number of PHYSICAL cores and processors.
  
  <Returns>
    The number of physical processors/cores, if there is insufficient
    data a default of 1 is returned.
  """
  cpu_cores = 0 # Stores integer value for number of cores
  cpu_physicalid = 0 # Stores the unique id's for the processors
  
  cpudefault = 1
  cpuinfo_copy = []
 
  try:
    openfile = open("/proc/cpuinfo", 'r') 
  except IOError:     
    return cpudefault

  # Read each line of the file and store it in a list, this is done 
  # because the contents of /proc/cpuinfo will be traversed up to 
  # two seperate times.
  for line in openfile:
    cpuinfo_copy.append(line)
  openfile.close()
      
  # get the number of cpu cores
  try:
    cpu_cores = count_Cores(cpuinfo_copy)
  except Exception:
    return cpudefault
  
  # get the number of physical id's 
  try:
    cpu_physicalid = count_ProcessorPhysicalId(cpuinfo_copy)
  except Exception:
    return cpudefault  
  
  # Refer to detailed explanation from program's opening comment.  
  return cpu_cores * cpu_physicalid
  
  
def get_cpu_virtual():
  """
  <Purpose>
    Measure the number of processors, this count includes both
    physical and virtual processors.
  
  <Returns>
    The number of physical processors/cores, if there is insufficient
    data a default of 1 is returned.
  """
  cpu_processors = 0 # Stores the number of processors
  cpudefault = 1
  cpuinfo_copy = []
 
  try:
    openfile = open("/proc/cpuinfo", 'r') 
  except IOError:     
    return cpudefault

  # get the number of processors
  try:
    cpu_processors = count_Processor(openfile)
  except Exception:
    return cpudefault 
  
  openfile.close()
  return cpu_processors


def get_memory():
  """
  <Purpose>
    get_memory will search the /proc/meminfo file on a linux
    system to find the size of RAM. Does not measure swap size
    because that has a seperate field in meminfo. 

  <Returns>  
    The size of RAM in bytes (converted from kB as it is stored in
    the meminfo file. If unable to open the file, or no valid data
    was retrieved, a default value is returned.
  """
  memory = ''
  memorydefault = 20000000
  
  try:
    openfile = open("/proc/meminfo", 'r') 
  except IOError:     
    return memorydefault

  # Search each line in the file for the line containing the
  # memory total.
  for line in openfile:
    if(line.find("MemTotal:") != -1):
      splitline = line.split()
      #example value for desired splitline
      #['MemTotal:', '2066344', 'kB']
      memory = splitline[1]
      openfile.close()  
     
      try:
        memory = long(memory)
      except ValueError:
        return memorydefault
      
      #Assuming memory will be stored in kB
      #memory is converted to bytes using 1KByte = 10^3 Bytes
      memory = memory * (10**3) 
      return memory  
  
  openfile.close()
  return memorydefault


def get_diskused():
  """
  <Purpose>
    Returns the total size in Bytes that are available on the 
    partition that the working directory is on.
  <Returns>
    The total number of Bytes available to the user on the current
    partition.
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
  except:
    return disksizedefault

  disksize = blocksize * freeblocks 
  return disksize 


def get_events():
  """
  <Purpose>
    Measure the maximum number threads the operating system will allow.
  """
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
  <Purpose>
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
