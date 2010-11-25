""" 
Author: Justin Cappos
Edited: Alan Loh

Module: A shell for Seattle called seash (pronounced see-SHH).   It's not meant
        to be the perfect shell, but it should be good enough for v0.1

Start date: September 18th, 2008

This is an example experiment manager for Seattle.   It allows a user to 
locate vessels they control and manage those vessels.

The design goals of this version are to be secure, simple, and reliable (in 
that order).   

Note: I've written this assuming that repy <-> python integration is perfect
and transparent (minus the bit of mess that fixes this).   As a result this
code may change significantly in the future.


Editor's Note: A large portion of seash's code has been separated into
different files. The only code remaining is the command loop that handles the 
user's input and the exception handling.

Command functions have been moved to command_callbacks.py. 

Helper functions and functions that operate on a target have been moved to 
seash_helper.py.

The newly implemented command dictionary, input parsing, and command dispatching 
have been moved to seash_dictionary.py.

Certain global variables are now kept track in seash_global_variables.py.

Besides the restructuring, the main change that has been made on seash is 
command input are now parsed according to the command dictionary. In addition,
with a structured database of sorts for commands, it should now be easier to 
implement new functions into seash as long as the correct format is followed in
implementing new commands.
"""


# Let's make sure the version of python is supported
import checkpythonversion
checkpythonversion.ensure_python_version_is_supported()

# Armon: Prevent all warnings
import warnings
# Ignores all warnings
warnings.simplefilter("ignore")

# simple client.   A better test client (but nothing like what a real client
# would be)

### Integration fix here...
from repyportability import *


tabcompletion = True
try:

  # Even we can import the readline module successfully, we still disable tab
  # completion in Windows, in response to Ticket #891.
  import os
  if os.name == 'nt':
    raise ImportError

  # Required for the tab completer. It works on Linux and Mac. It does not work
  # on Windows. See http://docs.python.org/library/readline.html for details. 
  import readline
except ImportError:
  print "Auto tab completion is off, because it is not available on your operating system."
  tabcompletion = False
  

# Needed for parsing user commands and executing command functions
import seash_dictionary

# For access to the global variables
import seash_global_variables

# To be able to catch certain exceptions thrown throughout the program
import seash_exceptions

import seash_helper

import repyhelper

repyhelper.translate_and_import("time.repy")

import traceback

import os.path    # fix path names when doing upload, loadkeys, etc.

import sys

#
# Provides tab completion of file names for the CLI, especially when running
# experiments. Able to automatically list file names upon pressing tab, offering
# functionalities similar to thoese of the Unix bash shell. 
#
# Define prefix as the string from the user input before the user hits TAB.
#
# TODO: If the directory or file names contain spaces, tab completion does not
# work. Also works for only Unix-like systems where slash is "/".
#
# Loosely based on http://effbot.org/librarybook/readline.htm
# Mostly written by Danny Y. Huang
#
class TabCompleter:



  # Constructor that initializes all the private variables
  def __init__(self):

    # list of files that match the directory of the given prefix
    self._words = []

    # list of files that match the given prefix
    self._matching_words = []

    self._prefix = None

    

  # Returns the path from a given prefix, by extracting the string up to the
  # last forward slash in the prefix. If no forward slash is found, returns an
  # empty string.
  def _getpath(self, prefix):

    slashpos = prefix.rfind("/")
    currentpath = ""
    if slashpos > -1:
      currentpath = prefix[0 : slashpos+1]

    return currentpath



  # Returns the file name, or a part of the file name, from a given prefix, by
  # extracting the string after the last forward slash in the prefix. If no
  # forward slash is found, returns an empty string.
  def _getfilename(self, prefix):

    # Find the last occurrence of the slash (if any), as it separates the path
    # and the file name.
    slashpos = prefix.rfind("/")
    filename = ""

    # If slash exists and there are characters after the last slash, then the
    # file name is whatever that follows the last slash.
    if slashpos > -1 and slashpos+1 <= len(prefix)-1:
      filename = prefix[slashpos+1:]

    # If no slash is found, then we assume that the entire user input is the
    # prefix of a file name because it does not contain a directory
    elif slashpos == -1:
      filename = prefix

    # If both cases fail, then the entire user input is the name of a
    # directory. Thus, we return the file name as an empty string.

    return filename



  # Returns a list of file names that start with the given prefix.
  def _listfiles(self, prefix):

    # Find the directory specified by the prefix
    currentpath = self._getpath(prefix)
    if not currentpath:
      currentpath = "./"
    filelist = []

    # Attempt to list files from the directory
    try:
      currentpath = os.path.expanduser(currentpath)
      filelist = os.listdir(currentpath)

    except:
      # We are silently dropping all exceptions because the directory specified
      # by the prefix may be incorrect. In this case, we're returning an empty
      # list, similar to what you would get when you TAB a wrong name in the
      # Unix shell.
      pass

    finally:
      return filelist



  # The completer function required as a callback by the readline module. See
  # also http://docs.python.org/library/readline.html#readline.set_completer
  def complete(self, prefix, index):

    # If the user updates the prefix, then we list files that start with the
    # prefix.
    if prefix != self._prefix:

      self._words = self._listfiles(prefix)
      fn = self._getfilename(prefix)

      # Find the files that match the prefix
      self._matching_words = []
      for word in self._words:
        if word.startswith(fn):
          self._matching_words.append(word)

      self._prefix = prefix

    try:
      return self._getpath(prefix) + self._matching_words[index]

    except IndexError:
      return None






def command_loop():

  # Things that may be set herein and used in later commands.
  # Contains the local variables of the original command loop.
  # Keeps track of the user's state in seash. Referenced 
  # during command executions by the command_parser.
  environment_dict = {
    'host': None, 
    'port': None, 
    'expnum': None,
    'filename': None,
    'cmdargs': None,
    'defaulttarget': None,
    'defaultkeyname': None,
    'currenttarget': None,
    'currentkeyname': None,
    'autosave': False,
    'handleinfo': {}
    }
  

  # Set up the tab completion environment (Added by Danny Y. Huang)
  if tabcompletion:
    completer = TabCompleter()
    readline.parse_and_bind("tab: complete")
    readline.set_completer_delims(" ")
    readline.set_completer(completer.complete)


  # exit via a return
  while True:

    try:
      
   
      # Saving state after each command? (Added by Danny Y. Huang)
      if environment_dict['autosave'] and environment_dict['defaultkeyname']:
        try:
          # State is saved in file "autosave_username", so that user knows which
          # RSA private key to use to reload the state.
          autosavefn = "autosave_" + str(environment_dict['defaultkeyname'])
          seash_helper.savestate(autosavefn, environment_dict['handleinfo'], environment_dict['host'], 
                                 environment_dict['port'], environment_dict['expnum'], 
                                 environment_dict['filename'], environment_dict['cmdargs'], 
                                 environment_dict['defaulttarget'], environment_dict['defaultkeyname'], 
                                 environment_dict['autosave'], environment_dict['defaultkeyname'])
        except Exception, error:
          raise UserError("There is an error in autosave: '" + str(error) + "'. You can turn off autosave using the command 'set autosave off'.")


      prompt = ''
      if environment_dict['defaultkeyname']:
        prompt = seash_helper.fit_string(environment_dict['defaultkeyname'],20)+"@"

      # display the thing they are acting on in their prompt (if applicable)
      if environment_dict['defaulttarget']:
        prompt = prompt + seash_helper.fit_string(environment_dict['defaulttarget'],20)

      prompt = prompt + " !> "
      # the prompt should look like: justin@good !> 

      # get the user input
      userinput = raw_input(prompt)
      
      if len(userinput)==0:
        continue
      
      # Returns the dictionary of dictionaries that correspond to the
      # command the user inputted
      cmd_input = seash_dictionary.parse_command(userinput)
      
      
      # by default, use the target specified in the prompt
      environment_dict['currenttarget'] = environment_dict['defaulttarget']
      
      # by default, use the identity specified in the prompt
      environment_dict['currentkeyname'] = environment_dict['defaultkeyname']

      # calls the command_dispatch method of seash_dictionary to execute the callback
      # method associated with the command the user inputed
      seash_dictionary.command_dispatch(cmd_input, environment_dict)


 

# handle errors
    except KeyboardInterrupt:
      # print or else their prompt will be indented
      print
      # Make sure the user understands why we exited
      print 'Exiting due to user interrupt'
      return
    except EOFError:
      # print or else their prompt will be indented
      print
      # Make sure the user understands why we exited
      print 'Exiting due to EOF (end-of-file) keystroke'
      return

    except seash_exceptions.ParseError, error_detail:
      print 'Invalid command input:', error_detail
    except seash_exceptions.DispatchError, error_detail:
      print error_detail
    except seash_exceptions.UserError, error_detail: 
      print error_detail
    except SystemExit:
      # exits command loop
      return
    except:
      traceback.print_exc()
      
  
  
if __name__=='__main__':
  time_updatetime(34612)
  command_loop()
