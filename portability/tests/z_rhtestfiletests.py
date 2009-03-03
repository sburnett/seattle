"""
Author: Andreas Sekine
Description:
  Tests the checks performed to determine whether or not a file needs to be
  retranslated. 
  
  Uses files of the form rhtestfiletests_n.repy
  
  No output indicates success
  
"""

import os
import repyhelper


def error(msg):
  print "ERROR:", msg
  

#this will provide a file with a more recent modtime 
tmp_filename = "rhtestfiletests_new.repy"
tmp_fh = open("rhtestfiletests_new.repy", "w")
print >> tmp_fh, repyhelper.TRANSLATION_TAGLINE
tmp_fh.close()

  
#Try some nonexistant files
try: 
  repyhelper._translation_is_needed("random_file246565324", tmp_filename)
  error("ERROR: nonexistant file passed")
except repyhelper.TranslationError, e:
  pass
  
try: 
  repyhelper._translation_is_needed("..", tmp_filename)
  error("directory passed test as file needing to be read")
except repyhelper.TranslationError, e:
  pass



#Now test the tagline
if repyhelper._translation_is_needed("rhtestfiletests_1.repy", tmp_filename):
  error("tagline detection (1) incorrectly passed, would have clobbered file")

#touch the file so it thinks translation is needed
os.utime("rhtestfiletests_2.repy", None)
if not repyhelper._translation_is_needed(tmp_filename, "rhtestfiletests_2.repy"):
  error("tagline detection (2) should have passed")
  
os.utime("rhtestfiletests_3.repy", None)
if repyhelper._translation_is_needed(tmp_filename, "rhtestfiletests_3.repy"):
  error("tagline detection (3) incorrectly passed")
  
  
os.remove(tmp_filename)

