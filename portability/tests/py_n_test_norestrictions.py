"""
Test to see if restrictions can be initialized and restored from within Python.

"""
from repyportability import *


import repyhelper



# in the call to this, it will do 'exitall' if the restrictions are in place
repyhelper.translate_and_import("rhtest_printifreadisfast.repy")

