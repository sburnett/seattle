"""
Test that the geoip module functions correctly.

"""
#pragma out
import os
# Make sure the geoip module is disabled before starting seash
if not 'geoip.disabled' in os.listdir('./modules/'):
  open('./modules/geoip.disabled', 'w')

import seash

commands = [
  'enable geoip',
  'disable geoip',
  'enable geoip',
  'loadkeys guest0',
  'as guest0',
  'browse',
  'on %1',
  'show location',
  'show coordinates'
]

seash.command_loop(commands)

# Make sure the geoip module is disabled after this run.
# This is to ensure that other modules' tests are not affected by this module.
seash.command_loop(['disable geoip'])