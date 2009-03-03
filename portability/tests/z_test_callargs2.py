"""
Test the callargs parameter of the translation calls, to make sure it actually
gets used

"""

import repyhelper
import test_utils

TESTFILE = "rhtest_callargs.repy"

#Make sure we have fresh translations per test run
translations = test_utils.get_translation_filenames([TESTFILE])
test_utils.cleanup_files(translations)

repyhelper.translate_and_import(TESTFILE, callargs=['a', 'samoas', 'c'])
if num_callargs() is not 3:
  print "translate_and_import had wrong number of callargs"


