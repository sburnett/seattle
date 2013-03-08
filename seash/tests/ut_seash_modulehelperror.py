"""
Make sure that showing information for a nonexistant module fails
"""
import seash

#pragma error Module is not installed
commands = [
  "modulehelp nonexistantmodule",
]
seash.command_loop(commands)