import os
import repyhelper

#this will provide a file with a more recent modtime 
new_filename = "rhtestfiletests_new.repy"
new_fh = open("rhtestfiletests_new.repy", "w")
print >> new_fh, repyhelper.TRANSLATION_TAGLINE
new_fh.close()

def error(msg):
  print "ERROR:", msg
  
  
#Try some nonexistant files
try: 
  repyhelper._translation_is_needed("random_file246565324", new_filename)
except repyhelper.TranslationError, e:
  pass
  
try: 
  repyhelper._translation_is_needed("..", new_filename)
except repyhelper.TranslationError, e:
  pass



#Now test the tagline
if repyhelper._translation_is_needed("rhtestfiletests_1.repy", new_filename):
  error("tagline detection (1) incorrectly passed, would have clobbered file")

#touch the file so it thinks translation is needed
os.utime("rhtestfiletests_2.repy", None)
if not repyhelper._translation_is_needed(new_filename, "rhtestfiletests_2.repy"):
  error("tagline detection (2) should have passed")
  
os.utime("rhtestfiletests_3.repy", None)
if repyhelper._translation_is_needed(new_filename, "rhtestfiletests_3.repy"):
  error("tagline detection (3) incorrectly passed")
  
os.remove(new_filename)

