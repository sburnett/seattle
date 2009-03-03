"""
Test the callfunc arg of the translations, to make sure it actually
gets used

"""

import repyhelper
import test_utils

TESTFILE = 'rhtest_callfunc.repy'

#Make sure we have fresh translations per test run
translations = test_utils.get_translation_filenames([TESTFILE])
test_utils.cleanup_files(translations)

modname = repyhelper.translate(TESTFILE, callfunc='plankton')
a = __import__(modname)

#Allow retranslation
test_utils.cleanup_files(translations)

repyhelper.translate_and_import(TESTFILE, callfunc='plankton')

