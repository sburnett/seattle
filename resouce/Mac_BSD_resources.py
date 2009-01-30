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
  files_open = 1000
  pipe = getShellPipe("sysctl kern.maxfiles")
  for line in pipe:
    line_s = line.split(" ")
    if len(line_s) > 1:
      files_open = int(line_s[1])
  pipe.close()

  # Get hard drive space, defaulting to 1 gig
  disk_space = 1000000000
  pipe = getShellPipe("df")
  seenFirstLine = False
  line_num = 0
  for line in pipe:
    line_num += 1
    if seenFirstLine:
      disk_space = 0  
      line_s = re.split("\\s*", line)
      if len(line_s) >= 6 and line:
        disk_space += (int(line_s[2]) + int(line_s[3])) * 1000
    else:
      seenFirstLine = True
  pipe.close()

  # Get the max number of processes, defaulting to 100
  events = 100
  pipe = getShellPipe("sysctl kern.maxproc")
  for line in pipe:
    line_s = line.split(" ")
    if len(line_s) > 1:
      events = int(line_s[1])
  pipe.close()
  
  print "resource cpu", num_cpu * 100
  print "resource memory", phys_mem
  print "resource filesopened", files_open
  print "resource diskused", disk_space
  print "resource events", events


if __name__ == "__main__":
    main()
