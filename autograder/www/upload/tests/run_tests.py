

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
import upload_assignment


#check general wrong arguments error
output=subprocess.Popen('python upload_assignment.py',shell=True,stdout=subprocess.PIPE)
if output.stdout.read().strip()!=upload_assignment.argErrorString:
  print "got unexpected output (for invalid arguments)"

#check file non-existence error
output=subprocess.Popen('python upload_assignment.py classcode em@il nonexistent_file',shell=True,stdout=subprocess.PIPE)
if output.stdout.read().strip()!="File doesn't exist\n"+upload_assignment.argErrorString:
  print "got unexpected output (for invalid arguments - nonexistent file)"

