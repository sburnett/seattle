"""
Ensure that when all modules do not conflict with each other

"""
import os

#pragma out Enabled modules:
#pragma out To see a list of all available modules, use the 'show modules' command.

import seash

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