"""
<Program Name>
  runcnctests.py

<Started>
  February 12, 2009
  
<Author>
  Cosmin Barsan
  
<purpose>
  This script runs all the CNC tests and prints out their output
  This script must be run from the same directory as the tests (which need to be in teh same directory as repyportability and its dependencies)
  the exec command function from prepare_test.py is used here.
  
<usage>
python runcnctests.py <server ip> <server port>

"""

import sys
import glob
import os
import shutil
import subprocess

def exec_command(command):
# Windows does not like close_fds and we shouldn't need it so...
  p =  subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

  # get the output and close
  theout = p.stdout.read()
  p.stdout.close()

  # get the errput and close
  theerr = p.stderr.read()
  p.stderr.close()

  # FreeBSD prints on stdout, when it gets a signal...
  # I want to look at the last line.   it ends in \n, so I use index -2
  if len(theout.split('\n')) > 1 and theout.split('\n')[-2].strip() == 'Terminated':
    # lose the last line
    theout = '\n'.join(theout.split('\n')[:-2])
    
    # however we threw away an extra '\n' if anything remains, let's replace it
    if theout != '':
      theout = theout + '\n'

  # everyone but FreeBSD uses stderr
  if theerr.strip() == 'Terminated':
    theerr = ''

  # Windows isn't fond of this either...
  # clean up after the child
#  os.waitpid(p.pid,0)

  return (theout, theerr)
  
def main():
  if len(sys.argv) < 3:
    print "invalid number of agruments"
    return

  
  ip = sys.argv[1]
  port = sys.argv[2]
  
  test_files = glob.glob("cnctest_*.py")
  
  print "\n"
  
  #count number of tests failede
  count=0
  
  #run each py file with prefix cnctest
  for file_path in test_files:
    print ("running test: " + file_path)
    (theout, theerr) =  exec_command("python " + file_path + " " + ip +" " + port)
    
    if theout.strip() != "done" :
      count=count+1
      
    print theout
    if theerr != "" :
      print "error output:"
      print theerr
    
    print "\n"
    
  print "runcnctests.py has completed, number of errors = " + str(count)


if __name__ == "__main__":
  main()
  