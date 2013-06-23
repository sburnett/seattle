"""
Ensure that when all modules do not conflict with each other

"""
#pragma out
import os
import seash

import seash_dictionary
import seash_modules
#pragma out Enabled modules: modules
seash_modules.enable_modules_from_last_session(seash_dictionary.seashcommanddict)


commands = [
  'loadkeys guest0',
  'as guest0',
  'browse',
  'on %1',
  # Enable all the modules
  'enable geoip',
  # Test geoip module
  'on %1 show location',
  'on %1 show coordinates',
  # Disable all the modules
  'disable geoip'
]

seash.command_loop(commands)