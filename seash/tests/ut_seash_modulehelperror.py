"""
Make sure that showing information for a nonexistant module fails
"""

# Seash's module system outputs a list of enabled modules on load.
# We need to instruct the UTF to ignore that.
#pragma out Enabled modules:
#pragma out To see a list of all available modules, use the 'show modules' command.
import seash

#pragma error Module is not installed
commands = [
  "modulehelp nonexistantmodule",
]
seash.command_loop(commands)