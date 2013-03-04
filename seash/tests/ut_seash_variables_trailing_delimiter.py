"""
Makes sure the Variables module for seash works as intended.
In particular, we check that trailing delimiters are not recognized as a
variable.
"""
#pragma out Enabled modules:
#pragma out To see a list of all available modules, use the 'show modules' command.

import seash

# This error should come up since %all contains nothing as we don't browse for
# anything prior to this.  This is not a problem though as we are just testing
# the trailing $ in a command.
#pragma error No targets to add (the target is already in '$')

seash.command_loop([
  'enable variables',
  'add %all to $'
])