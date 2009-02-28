"""
  <Program Name>
    Mac_BSD_resources.py

  <Started On>
    January 2009

  <Author>
    Carter Butaud

  <Purpose>
    Runs ons a Mac or BSD system to benchmark important resources.
"""


import subprocess
import re
#import bandwidth

def getShellPipe(cmd):
    return subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE).stdout

def main():
    
  #First, get number of CPUs, defaulting to 1
  num_cpu = 1
  pipe = getShellPipe("sysctl hw.ncpu")
  for line in pipe:
    line_s = line.split(" ")
    if len(line_s) > 1:
      num_cpu = int(line_s[1])
  pipe.close()

  # Next, get physical memory (RAM), defaulting to 1 gig
  phys_mem = 1000000000
  pipe = getShellPipe("sysctl hw.physmem")
  for line in pipe:
    line_s = line.split(" ")
    if len(line_s) > 1:
      phys_mem = int(line_s[1])
  pipe.close()

  # Get max files open, defaulting to 1000
  # Make sure that 10% of the total system
  # is not more than the per process limit
  files_open = 1000
  files_open_per_proc = False
  files_open_total = False
  pipe = getShellPipe("sysctl kern.maxfiles")
  for line in pipe:
    line_s = line.split(" ")
    if len(line_s) > 1:
      files_open_total = int(line_s[1])
  pipe.close()
  pipe = getShellPipe("sysctl kern.maxfilesperproc")
  for line in pipe:
    line_s = line.split(" ")
    if len(line_s) > 1:
      files_open_per_proc = int(line_s[1])
  pipe.close()
  if files_open_per_proc and files_open_total:
    files_open = min(files_open_per_proc * 10, files_open_total)
  elif files_open_per_proc:
    files_open = 10 * files_open_per_proc
  elif files_open_total:
    files_open = files_open_total


  # Get hard drive space, defaulting to 1 gig
  disk_space = 1000000000
  pipe = getShellPipe("df -k .")
  seenFirstLine = False
  for line in pipe:
    if seenFirstLine:  
      line_s = re.split("\\s*", line)
      if len(line_s) >= 6 and line:
        disk_space = (int(line_s[3])) * 1024
    else:
      seenFirstLine = True
  pipe.close()

  # Get the max number of processes, defaulting to 100
  events = 100
  pipe = getShellPipe("sysctl kern.maxprocperuid")
  for line in pipe:
    line_s = line.split(" ")
    if len(line_s) > 1:
      events = int(line_s[1])
  pipe.close()

  # Get the max number of sockets, defaulting to 512
  maxsockets = 512
  pipe = getShellPipe("sysctl kern.ipc.maxsockets")
  for line in pipe:
    line_s = line.split(" ")
    if len(line_s) > 1:
      maxsockets = int(line_s[1])
  pipe.close()

  # Get the available bandwidth, defaulting to 100000
  """my_bandwidth = 100000
  server_ip = "128.208.1.137"
  try:
    my_bandwidth = bandwidth.get_bandwidth(server_ip)
  except:
    pass"""
  
  print "resource cpu", num_cpu
  print "resource memory", phys_mem
  print "resource filesopened", files_open
  print "resource diskused", disk_space
  print "resource events", events
  print "resource insockets", maxsockets / 2
  print "resource outsockets", maxsockets / 2
  #print "resource netsend", my_bandwidth
  #print "resource netreceive", my_bandwidth


if __name__ == "__main__":
    main()
