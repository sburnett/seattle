"""
Makes sure the Variables module for seash works as intended.
In particular, we check that the $varname and $varname$ methods of referencing
variables are functional.
"""

#pragma out
import seash

seash.command_loop([
  'enable variables',
  'set helpcmd help',
  '$helpcmd',
  '$helpcmd show',
  '$helpcmd$',
  '$helpcmd$ show',
  'disable variables',
])