"""
Test to make sure specifying that modules have a shared mycontext 
"""

import repyhelper
import test_utils


TESTFILE1 = "rhtest_mycontext1.repy"
TESTFILE2 = "rhtest_mycontext2.repy"

translations = test_utils.get_translation_filenames([TESTFILE1, TESTFILE2])
test_utils.cleanup_files(translations)


modname1 = repyhelper.translate(TESTFILE1, shared_mycontext=True)
mod1 = __import__(modname1)

modname2 = repyhelper.translate(TESTFILE2, shared_mycontext=True)
mod2 = __import__(modname2)

if mod2.foo() is 'bar':
  pass
else:
  print "Context sharing failed! foo returned", mod2.foo()

