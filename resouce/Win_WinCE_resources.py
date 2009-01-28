# Generates some resource info for Windows and Windows Mobile

# Windows Mobile Info

# CPU's: 1
# Max Processes: 32
# Max Threads: Bound by Memory, default is 1 meg per tread, so 32 max
# This would essentially leave no memory for anything else, so lets do 1/4
# See: http://msdn.microsoft.com/en-us/library/bb202727.aspx
# Max Memory: Windows Mobile 5 limit is 32 megs per app
# Mobile 6 is 1 gig, but lets play it safe
# http://www.addlogic.se/articles/articles/windows-ce-6-memory-architecture.html
# I can't find a handle limit for Mobile, but lets just use 1/4 of desktop (50)

# Windows Info
# CPU's: %NUMBER_OF_PROCESSORS%
# Processes: I think I remember 32K
# Threads: 512 default, we will probably hit a memory limit first so...
# Lets do 1/4 of this, times the number of CPU's
# http://msdn.microsoft.com/en-us/library/ms684957.aspx
# Max Memory: 4 gigs on 32bit, but getMem info can handle up to 64 gig for 64bit machines

# 10,000 File handle limit on Windows XP, but see object limit
# See: http://support.microsoft.com/kb/327699
# Total user objects can be between 200 and 65K
# See: http://msdn.microsoft.com/en-us/library/ms725486(VS.85).aspx
# So, lets use the lowest possible to play it safe

# Loopback is a special case of network, we can do the same benchmark with a local addr

import windows_api

# Get disk info, using current directory
diskInfo = windows_api.diskUtil(None)
totalDisk = diskInfo["totalBytes"]
freeDisk = diskInfo["freeBytes"]
  
# Get meminfo
if windows_api.MobileCE:
  totalMem = 32*1024*1024 # 32 Meg limit
else:
  memInfo = windows_api.globalMemoryInfo()
  totalMem = memInfo["totalPhysical"]
  
# Default to 1, for WinCE
numCPU = 1

# Don't even bother on WinCE
if not windows_api.MobileCE:
  try:
    import subprocess
  
    cmd="echo %NUMBER_OF_PROCESSORS%"
    proc=subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
  
    output = proc.stdout.read()
    proc.stdout.close()
    # Attempt to parse output for a number of CPU's
    if len(output) != 0:
      num=int(output)
      if num >= 1:
        numCPU = num      
      
  except:
    pass

if windows_api.MobileCE:
  threadMax = 8
else:
  # Hard limit at 512
  threadMax = min(128*numCPU,512)
  
handleMax = 100 # Half of the object limit

# Assume 1/4th on Mobile
if windows_api.MobileCE:
  handleMax = handleMax / 4

socketMax = handleMax # Half of the object limit

print "resource cpu ", numCPU
print "resource memory ", totalMem
print "resource diskused ", freeDisk
print "resource events ", threadMax
print "resource filesopened ", handleMax
print "resource insockets ", socketMax/2
print "resource outsockets ", socketMax/2


