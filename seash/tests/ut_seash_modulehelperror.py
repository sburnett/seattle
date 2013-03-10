"""
Make sure that showing information for a nonexistant module fails
"""
import seash
import seash_dictionary
import seash_modules


#pragma out Enabled modules: modules
#pragma out To see a list of all available modules, use the 'show modules' command.
seash_modules.enable_modules_from_last_session(seash_dictionary.seashcommanddict)

#pragma error Module is not installed
commands = [
  "modulehelp nonexistantmodule",
]
seash.command_loop(commands)