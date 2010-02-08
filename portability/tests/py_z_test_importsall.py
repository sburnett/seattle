"""
Author: Justin Cappos
Description
  Should import all names from an included python program
  
  No output indicates success

"""

myname = __name__

import repyhelper

repyhelper.translate_and_import('rhtestname_oddnames.repy')

# these should all be defined now...
name1
name2
_name3

# don't change the __ mappings because bad things happen!   
assert(myname == __name__)

