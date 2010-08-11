import repyhelper
import os
import sys
import resource
import time
if not os.path.exists('nodemanager.repyhelpercache'):
  os.mkdir('nodemanager.repyhelpercache')
sys.path = ['nodemanager.repyhelpercache'] + sys.path
repyhelpercachedir = repyhelper.set_importcachedir('nodemanager.repyhelpercache')
import warnings
warnings.simplefilter("ignore")
from repyportability import *

#repyhelper.translate_and_import("ShimStackInterface.repy")


CALLS = 100

def fun(n):
  shimstr = '(NoopShim)' * n
  #client = ShimStack(shimstr)
  sock = openconn('127.8.9.0', 12345)

  starttime = getruntime()
  for i in range(CALLS):
    sock.send('x')
  endtime = getruntime()
  
  sock.close()
  #DummyDNSStop()

  time = int((endtime - starttime) * 1000 * 1000 / CALLS) # in microseconds
  return (time, getmem())


def getmem():
  pid = os.getpid()
  memfile = open('/proc/%d/status' % pid, 'r')
  for line in memfile.readlines():
    if line.startswith('VmPeak:'):
      line = line.replace('VmPeak:', '')
      line = line.replace('kB', '')
      line = line.strip()
      vmpeak = int(line)
      break
  memfile.close()
  return vmpeak


sys.setrecursionlimit(65535)
try:
  n = int(sys.argv[1])
except:
  print "Wrong parameter"
  exit()

ret = fun(n)
print ret[0], ',', ret[1]
