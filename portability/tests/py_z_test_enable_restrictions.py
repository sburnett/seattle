"""
Test to see if restrictions can be initialized and restored from within Python.

"""
from repyportability import *

initialize_restrictions("restrictions.veryslowread")

import repyhelper

override_restrictions()
enable_restrictions()


# in the call to this, it will do 'exitall' if the restrictions are in place
repyhelper.translate_and_import("printifreadisfast.repy")

