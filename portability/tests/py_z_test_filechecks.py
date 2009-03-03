"""
Author: Andreas Sekine
Description:
  Tests the checks performed to determine whether or not a file needs to be
  retranslated.
  
  The following are checked:
    -Both arguments for whether or not the file exists
    -If a directory is provided as an argument
    -
  
  No output indicates success
  
"""

import os
import repyhelper
  
#The (preexisting) repy file to use as a reference for translating
SRCFILE = "rhtest_filetests.repy"
#The temporary file to create to perform checks against
TESTFILE = "rhtest_filetests_new.repy"
#The translation name corresponding to TESTFILE
TESTFILE_TR = repyhelper._get_module_name(TESTFILE) + ".py"


#delete file if it exists
def clean_file(name):
  if os.path.isfile(name):
    os.remove(name)


def create_testfile(filename, file_tag):
  """
  Create a file in the current directory with a specified translation tagline file tag
  returns the name of the created file
  """
  fh = open(filename, 'w')
  print >> fh, repyhelper.TRANSLATION_TAGLINE, file_tag
  fh.close()
  return filename
  
  
create_testfile(TESTFILE, "")

### Test Nonexistant Files ###

if repyhelper._translation_is_needed(SRCFILE, "file_doesnt_exist'"):
  pass
else:
  print "Test failed for translation path that doesn't exist'"

clean_file(TESTFILE_TR)

#Test source (repy) file
try: 
  repyhelper._translation_is_needed("random_file246565324", TESTFILE)
except repyhelper.TranslationError:
  pass
else:
  print "test didnt raise exception when provided bad souce file"

clean_file(TESTFILE_TR)

create_testfile(TESTFILE, "")

#Test directory...
try: 
  repyhelper._translation_is_needed("..", TESTFILE)
except repyhelper.TranslationError:
  pass
else:
  print "directory passed test as file needing to be read"

clean_file(TESTFILE_TR)



### Now test the tagline tests ###

#Create a file without the tagline, to see if an anonomous file would get clobbered
fh = open(TESTFILE, "w")
fh.write("gibberish!")
fh.close()
try:
  repyhelper._translation_is_needed(SRCFILE, TESTFILE)
except repyhelper.TranslationError:
  pass
else:
  print "tagline detection incorrectly passed, would have clobbered file"

clean_file(TESTFILE_TR)



#create a fake translation with the correct flag, and a newer modification time
#on the source. This means the test should pass
create_testfile(TESTFILE, os.path.abspath(SRCFILE))
#touch the source file so it thinks translation is needed
os.utime(SRCFILE, None)
if repyhelper._translation_is_needed(SRCFILE, TESTFILE):
  pass
else:
  print "tagline detection should have passed, but failed"
  
clean_file(TESTFILE_TR)


#Perform the same tests as last (valid translation file), but keep modtime of
#translation newer, so test should fail
create_testfile(TESTFILE, os.path.abspath(SRCFILE))
if repyhelper._translation_is_needed(SRCFILE, TESTFILE):
  pass
else:
    print "file modification time tests failed!"


#Test the file path check for a bogus path
create_testfile(TESTFILE, "badfiletag")  
os.utime(SRCFILE, None)
try:
  repyhelper._translation_is_needed(SRCFILE, TESTFILE)
except repyhelper.TranslationError:
  pass
else:
  print "Bogus file path check failed"  
  
clean_file(TESTFILE_TR)

