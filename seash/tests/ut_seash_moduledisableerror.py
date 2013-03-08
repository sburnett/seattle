"""
Make sure that disabling a disabled module fails
"""

import seash

#pragma error Module is not enabled
commands = [
  "disable geoip",
  "disable geoip"
]
seash.command_loop(commands)