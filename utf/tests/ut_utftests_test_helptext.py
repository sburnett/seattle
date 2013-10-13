"""
When utf.py is run without any options, a help text is printed out with available options.

This test will check if all options of the utf.py module is printed out in the help text.
We run the utf.py in python shell and capture its output to check for errors.
The pragmas below must be updated when ever options are added or removed in utf.py
"""

#pragma out 
#pragma out Options:
#pragma out   -h, --help            show this help message and exit
#pragma out 
#pragma out   Generic:
#pragma out     -v, --verbose       verbose output
#pragma out     -T, --show-time     display the time taken to execute a test.
#pragma out 
#pragma out   Testing:
#pragma out     -m MODULE, --module=MODULE
#pragma out                         run tests for a specific module
#pragma out     -f FILE, --file=FILE
#pragma out                         execute a specific test file
#pragma out     -a, --all           execute all test files

import subprocess
import sys

sub = subprocess.Popen([sys.executable, 'utf.py'], 
  stderr=subprocess.PIPE, 
  stdout=subprocess.PIPE)
(out, err) = sub.communicate()


# If error was generated, it will be printed below
# We are interested in the help text that is printed in stdout
# The pragmas are used to compare if this matches the expected output
if err:
  print>>sys.stderr, "FAIL: test produced on standard out ", err
else:
  print out