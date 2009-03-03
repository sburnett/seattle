"""
Author: Andreas Sekine
Description:
  Perform various tests on recursive/circular includes/imports/translates
  
  Uses files of the form rhtestrecursion_n.repy
  
  No output indicates success
  
"""

import repyhelper

#This tests circular includes
translation = repyhelper.translate("rhtestrecursion_1.repy")
if translation == "":
  print "Error translating circular recursion"
else:
  #actually include it to make sure the translation was valid
  __import__(translation)
 

  
  
#Tests self include  
translation = repyhelper.translate("rhtestrecursion_4.repy")
if translation == "":
  print "Error translating self-include"
else:
  __import__(translation)
