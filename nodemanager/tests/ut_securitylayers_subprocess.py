import subprocess
import sys
import harshexit
import os
import shutil
import glob
import time
import persist
import sys

# initialize directory for security layer files
if os.path.exists("securitylayers"):
  shutil.rmtree("securitylayers")
os.mkdir("securitylayers")
shutil.copy("private_encasementlib.repy", "securitylayers")
shutil.copy("private_wrapper.repy", "securitylayers")
shutil.copy("private_hideprivate_layer.repy", "securitylayers")

initproc = subprocess.Popen([sys.executable, "nminit.py"])
initproc.wait()

# nminit doesn't automatically initialize the vessels with security layer files,
# so we should do this ourselves
for vesseldirectoryname in glob.glob('v[0-9]*'):
  if os.path.isdir(vesseldirectoryname):
    shutil.rmtree(vesseldirectoryname)
    shutil.copytree("securitylayers", vesseldirectoryname)

# add security layer configuration to nodeman.cfg
configuration = persist.restore_object("nodeman.cfg")
configuration['repy_prepend'] = ["private_encasementlib.repy", "private_hideprivate_layer.repy"]
configuration['repy_prepend_dir'] = "securitylayers"
persist.commit_object(configuration, "nodeman.cfg")

nmproc = subprocess.Popen([sys.executable, "nmmain.py", "--test-mode"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# without closing stdin, stdout, stderr, nmmain.py won't execute on XP
nmproc.stdin.close()
nmproc.stdout.close()
nmproc.stderr.close()

try:
  # We'll want to kill this once we are told to do so... (sys.stdin.close() is
  # the signal)
  sys.stdin.read()
except KeyboardInterrupt:
  # the user interrupted us, let's clean up!
  print
  print 'Cleaning up the subprocess'

# We need the PID.   Since the node manager daemonizes, this isn't the pid of
# nmproc.   We can get the PID from the log
nodemanagerlogfo = open('v2'+os.sep+'nodemanager.old')

firstline = nodemanagerlogfo.readline()

# an entry looks like this:
# 1292537407.82:PID-27493:[INFO]: Running nodemanager in test mode
# let's get the PID out as a number...
pidportion = firstline.split(':')[1]
assert(pidportion.startswith('PID-'))
nmpid = int(pidportion[4:])

# let's terminate the node manager...
harshexit.portablekill(nmpid)
