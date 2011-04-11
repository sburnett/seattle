
# I'm importing these so I can neuter the calls so that they aren't 
# restricted...
import safe
import nanny
import emulfile
import emulmisc
import namespace
import nonportable
import virtual_namespace


# JAC: Save the calls in case I want to restore them.   This is useful if 
# repy ends up wanting to use either repyportability or repyhelper...
# This is also useful if a user wants to enforce restrictions on the repy
# code they import via repyhelper (they must use 
# restrictions.init_restriction_tables(filename) as well)...
oldrestrictioncalls = {}
oldrestrictioncalls['nanny.tattle_quantity'] = nanny.tattle_quantity
oldrestrictioncalls['nanny.tattle_add_item'] = nanny.tattle_add_item
oldrestrictioncalls['nanny.tattle_remove_item'] = nanny.tattle_remove_item
oldrestrictioncalls['nanny.is_item_allowed'] = nanny.is_item_allowed
oldrestrictioncalls['nanny.get_resource_limit'] = nanny.get_resource_limit
oldrestrictioncalls['emulfile.assert_is_allowed_filename'] = emulfile._assert_is_allowed_filename


def _do_nothing(*args):
  pass

def _always_true(*args):
  return True


# Overwrite the calls so that I don't have restrictions (the default)
def override_restrictions():
  """
   <Purpose>
      Turns off restrictions.   Resource use will be unmetered after making
      this call.   (note that CPU / memory / disk space will never be metered
      by repyhelper or repyportability)

   <Arguments>
      None.
         
   <Exceptions>
      None.

   <Side Effects>
      Resource use is unmetered / calls are unrestricted.

   <Returns>
      None
  """
  nanny.tattle_quantity = _do_nothing
  nanny.tattle_add_item = _do_nothing
  nanny.tattle_remove_item = _do_nothing
  nanny.is_item_allowed = _always_true
  nanny.get_resource_limit = _do_nothing
  emulfile.assert_is_allowed_filename = _do_nothing
  


# Sets up restrictions for the program
# THIS IS ONLY METERED FOR REPY CALLS AND DOES NOT INCLUDE CPU / MEM / DISK 
# SPACE
def initialize_restrictions(restrictionsfn):
  """
   <Purpose>
      Sets up restrictions.   This allows some resources to be metered 
      despite the use of repyportability / repyhelper.   CPU / memory / disk 
      space will not be metered.   Call restrictions will also be enabled.

   <Arguments>
      restrictionsfn:
        The file name of the restrictions file.
         
   <Exceptions>
      None.

   <Side Effects>
      Enables restrictions.

   <Returns>
      None
  """
  nanny.start_resource_nanny(restrictionsfn)

def enable_restrictions():
  """
   <Purpose>
      Turns on restrictions.   There must have previously been a call to
      initialize_restrictions().  CPU / memory / disk space will not be 
      metered.   Call restrictions will also be enabled.

   <Arguments>
      None.
         
   <Exceptions>
      None.

   <Side Effects>
      Enables call restrictions / resource metering.

   <Returns>
      None
  """
  # JAC: THIS WILL NOT ENABLE CPU / MEMORY / DISK SPACE
  nanny.tattle_quantity = oldrestrictioncalls['nanny.tattle_quantity']
  nanny.tattle_add_item = oldrestrictioncalls['nanny.tattle_add_item'] 
  nanny.tattle_remove_item = oldrestrictioncalls['nanny.tattle_remove_item'] 
  nanny.is_item_allowed = oldrestrictioncalls['nanny.is_item_allowed'] 
  nanny.get_resource_limit = oldrestrictioncalls['nanny.get_resource_limit']
  emulfile.assert_is_allowed_filename = oldrestrictioncalls['emulfile.assert_is_allowed_filename']
  
# from virtual_namespace import VirtualNamespace
# We need more of the module then just the VirtualNamespace
from virtual_namespace import *
from safe import *
from emulmisc import *
from emulcomm import *
from emulfile import *
from emultimer import *

# Buld the _context and usercontext dicts.
# These will be the functions and variables in the user's namespace (along
# with the builtins allowed by the safe module).
usercontext = {'mycontext':{}}

# Add to the user's namespace wrapped versions of the API functions we make
# available to the untrusted user code.
namespace.wrap_and_insert_api_functions(usercontext)

# Convert the usercontext from a dict to a SafeDict
usercontext = safe.SafeDict(usercontext)

# Allow some introspection by providing a reference to the context
usercontext["_context"] = usercontext
usercontext["getresources"] = nonportable.get_resources
usercontext["createvirtualnamespace"] = virtual_namespace.createvirtualnamespace
usercontext["getlasterror"] = emulmisc.getlasterror
_context = usercontext.copy()

# This is needed because otherwise we're using the old versions of file and
# open.   We should change the names of these functions when we design
# repy 0.2
originalopen = open
originalfile = file
openfile = emulated_open

# file command discontinued in repy V2
#file = emulated_open

# Override by default!
override_restrictions()

