"""
Make sure that disabling a disabled module fails
"""

# Seash's module system outputs a list of enabled modules on load.
# We need to instruct the UTF to ignore that.
#pragma out Enabled modules:
#pragma out To see a list of all available modules, use the 'show modules' command.
import seash

#pragma error Module is not enabled
commands = [
  "disable geoip",
  "disable geoip"
]
seash.command_loop(commands)