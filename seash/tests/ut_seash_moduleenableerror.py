"""
Make sure that disabling a disabled module fails
"""
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