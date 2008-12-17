"""
Author: Andreas Sekine
Description
  Tests various file name formats for calls to translate
  
"""
import os
import repyhelper


def prepare_file(filename):
  #make an empty test file of name filename
  try:
    fh = open(filename, "w")
    fh.close()
    return True
  except IOError, e:
    print "Error opening file for test:", filename
    return False
    
def cleanup(filename):
  if os.path.isfile(filename):
    os.remove(filename)
  else:
    print "Couldn't cleanup file", filename
    
def test_name(name, expected):
  if prepare_file(name):
    translation_name = repyhelper.translate(name)
    
    if translation_name != expected:
      print "ERROR: expected:", expected, "translation:", translation_name
      
    cleanup(name)

    cleanup(translation_name + ".py")



test_name("rhtestname_file1.repy", "rhtestname_file1_repy")
test_name("rhtestname_file2.py", "rhtestname_file2_py")
test_name("rhtestname.file3.py", "rhtestname_file3_py")
test_name("rhtestname.file4.repy", "rhtestname_file4_repy")
test_name("rhtestname file5.repy", "rhtestname file5_repy")


