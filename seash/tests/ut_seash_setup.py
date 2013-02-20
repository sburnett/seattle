"""
Makes sure that vessels on the nodemanager are accessible before continuing with
the unit tests.  This is essential so that the first few unit tests don't fail 
because the node manager isn't ready yet.

"""

import repyhelper
repyhelper.translate_and_import('rsa.repy')
repyhelper.translate_and_import('advertise.repy')

for guestnum in xrange(4):
  guestkey = rsa_file_to_publickey('guest'+str(guestnum)+'.publickey')
  while not advertise_lookup(guestkey, graceperiod=1):
    sleep(2)