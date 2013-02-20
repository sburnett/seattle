"""
Make sure that disabling a disabled module fails
"""

# Seash's module system outputs a list of enabled modules on load.
# We need to instruct the UTF to ignore that.
#pragma out Enabled modules:
#pragma out To see a list of all available modules, use the 'show modules' command.
import seash
import seash_exceptions


seash.command_loop(["enable geoip"])

# This should fail.  We can't use the built in UTF pragma because we need to 
# disable the module before we finish this test.
try:
  seash.command_loop(["enable geoip"])
except seash_exceptions.UserError, e:
  if "Module is already enabled." not in str(e):
    raise

seash.command_loop(["disable geoip"])