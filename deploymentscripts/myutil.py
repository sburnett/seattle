#! /usr/bin/env python2.3

import os
import sys


def print_run(cmd):
  print cmd
  return os.system(cmd)



def exec_list(func, list):
  for item in list:
    func(item)


def do_file(func, fulllist, forkthreads = 10):
  
  list = []
  for num in range(forkthreads):
    list.append([])

  thread = 0
  for line in fulllist:
    list[thread%forkthreads].append(line.strip())
    thread = thread + 1
  
  for num in range(forkthreads):
    if os.fork()==0:
      if num<len(list):
        exec_list(func,list[num])
        os._exit(0)
  
  for num in range(forkthreads):
    if num<len(list):
      os.wait()
  
