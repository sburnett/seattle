"""
Makes sure that vessels on the nodemanager are accessible before continuing with
the unit tests.  This is essential so that the first few unit tests don't fail 
because the node manager isn't ready yet.

Also disables all modules so that individual module tests can assume a clean
module system before running.
"""

# Disable all modules.
# We pass in an empty dict because we only care that the .disabled file gets 
# created
import seash_modules
for module in seash_modules.get_enabled_modules():
  seash_modules.disable({}, module)

import repyhelper
repyhelper.translate_and_import('rsa.repy')
repyhelper.translate_and_import('advertise.repy')

for guestnum in xrange(4):
  guestkey = rsa_file_to_publickey('guest'+str(guestnum)+'.publickey')
  while not advertise_lookup(guestkey, graceperiod=1):
    sleep(2)