
import subprocess
import os

import utfutil

import sys

# Make sure repy.py works when invoked with options in a various 
# order (to test that adding getopt worked.)

def main():
  args = [sys.executable, 'repy.py', 
          '--simple', 
          '--logfile', 'log.log', 
          'restrictions.loose', 
          'test_options.py']

  test_process = subprocess.Popen(args)
  test_process.wait()

  # Check that log was created.
  if os.path.exists("log.log.old"): 

    os.remove("log.log.old")

    opposite_args = [sys.executable,    'repy.py',
                     '--logfile', 'log.log', 
                     '--simple', 
                     'restrictions.loose', 
                     'test_options.py']

    test_process = subprocess.Popen(opposite_args)
    test_process.wait()
    
    # Check that log was created (again).
    if not os.path.exists("log.log.old"):
      print 'Passing arguments in the opposite order failed.'

  else: 
    print 'Test for passing arguments in the opposite order failed.'




if __name__ == "__main__":
  main()
