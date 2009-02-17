

"""
<Program Name>
  run_tests.py

<Started>
  February 1, 2009

<Author>
  Salikh Bagaveyev

<Purpose>
  Unit test for upload_assignment.py
"""

import subprocess
import testsDeployRun
import os


badArgsError="Invalid arguments - usage: python testsDeployRun.py [iplist_file]"

#check general wrong arguments error
output=subprocess.Popen('python testsDeployRun.py',shell=True,stdout=subprocess.PIPE)
if output.stdout.read().strip()!=badArgsError:
  print "got unexpected output (for invalid arguments)"

#check if provided is a folder
if (os.path.isdir("logs"))==False:
  print "logs folder should exist"


