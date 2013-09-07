"""
Test that we can acquire and release vessels.

"""
import seash
import sys

# We need the modules module
import seash_modules
import seash_dictionary
#pragma out Enabled modules: modules
#pragma out You must have M2Crypto installed to connect to the Clearinghouse securely.
#pragma out Insecure mode will be used for the rest of this session.

#pragma out Added group 'acquired' with 5 targets
#pragma out acquired (empty)

seash_modules.enable_modules_from_last_session(seash_dictionary.seashcommanddict)

commands = [
  'enable clearinghouse',
  'loadkeys seash_gettest',
  'as seash_gettest',
  'get 5',
  'on acquired',
  'release acquired',
  'show targets',
]

# Allow the geoip module to be disabled when done,
# even if exceptions occur
try:
  seash.command_loop(commands)
except Exception, e:
  print>>sys.stderr, str(e)

# Make sure the geoip module is disabled after this run.
# This is to ensure that other modules' tests are not affected by this module.
seash.command_loop(['disable clearinghouse'])