"""
Author: Alan Loh

Module: A data structure of all the available commands of seash held in a
        dictionary of dictionaries format. Also holds the methods for
        parsing user command input and executing functions corresponding
        to the command.

User input is parsed according to whether or not it follows the structure 
of a command's dictionary and its children.  When parsing a command word, 
it simply checks to see if the user's input string list contains the command word 
at the appropriate index respective to the level of command dictionary currently
being iterated. If it is an user argument, however, it will
simply assign the user's inputted string as the key of the respective
argument's dictionary.

Command input is split by white spaces, so except for the case of arguments 
located at the end of the command string series, the parser will not taken 
into account file names or arguments that are multiple words long. Also, 
because of the way the command callback functions pull out user arguments, 
arguments of similar type need different 'name' field in its command dictionary
to help distinguish one from the other.
"""


# for access to list of targets
import seash_global_variables

import seash_exceptions

import command_callbacks



"""
Command dictionary entry format:
  '(command key)':{'name':'', 'callback':, 'priority':, 'help_text':'', 'children':[

'(command key)' - The expected command word the user is suppose to input to
call the command's function. If a certain type of argument is expected, a general
word in all caps should be enclosed within square brackets that signify the type 
of argument needed. For example, '[TARGET]' if a target ID is expected, or 
'[FILENAME]' if the name of a file is needed. Frequently used type includes 
'[TARGET]' for targets, '[KEYNAME]' for loaded keynames, '[FILENAME]' for files,
and '[ARGUMENT]' for everything else, so unless another category of arguments is 
needed, only use those four strings for command keys of arguments in order for 
the parser to work correctly.
 
For general commands like 'browse', however, the key would simply be the same 
command word, 'browse'. 

In general, the command key should only be a single word from the whole command 
string being implemented, and with the exception of Arguments that occur at the 
end of the command string, no user-inputted arguments should ever contain spaces.


'name':       - The name of the command word. For general commands, it should be 
the same as the command key. For arguments, however, the name should be 
distinguishable from other potential arguments of the same command key to avoid 
conflicts when pulling the user's argument from the input dictionary during 
command execution.


'callback':     - Reference to the command callback function associated with the
command string up to this point. Only command dictionaries that mark a complete 
command string should contain a reference to a callback method. Otherwise, it 
should be set to none. Default location of command callback functions is 
command_callbacks.py.


'priority'      - Gives the command callback function of the dictionary 
containing the key 'priority' the priority of being executed first before 
executing the main function of the command string. It should be implemented and 
assigned True if needed. Otherwise, it should not be added into any other command
dictionary.

An example of how it should work is in the case of 'as [KEYNAME] browse':
A keyname needs to be set before executing 'browse', so the command dictionary of
'[KEYNAME]' has 'priority' in being executed first to set the user's keyname 
before executing 'browse's command function.


'help_text'     - The text that will be outputted whenever a user accesses the 
help function for that command. Not every command dictionary needs a help text
associated with it, so it defaults as a blank string, and if none of the command 
dictionaries in the help call holds a help text, it will default at the last 
command dictionary that holds one, namely the dictionary associated with 'help'.


'children'      - The list of command dictionaries that follows the current one.
This will determine the validity of an command input when parsing. Each user
inputted string is verified that it follows one of the potential chains of 
command strings through the series of command dictionaries. Limit only one
argument dictionary per children list to avoid confusion when parsing user
argument input.
 
For example, in the command 'show resources', the children of the command 
dictionary for 'show' will contain the command dictionary 'resources' along with
any other potential command words that can follow 'show'.

"""


seashcommanddict = {
  'on':{'name':'on', 'callback':None, 'help_text':'', 'children':{
      '[TARGET]':{'name':'ontarget', 'callback':command_callbacks.on_target, 'priority':True, 'help_text':'', 'children':{
      }}
  }},


  'as':{'name':'as', 'callback':None, 'help_text':'', 'children':{
      '[KEYNAME]':{'name':'askeyname', 'callback':command_callbacks.as_keyname, 'priority':True, 'help_text':'', 'children':{
      }},
  }},


  'help':{'name':'help', 'callback':command_callbacks.help, 'priority':True, 'help_text':"""
A target can be either a host:port:vesselname, %ID, or a group name.

on target [command] -- Runs a command on a target (or changes the default)
as keyname [command]-- Run a command using an identity (or changes the default).
add [target] [to group]      -- Adds a target to a new or existing group 
remove [target] [from group] -- Removes a target from a group
show                -- Displays shell state (use 'help show' for more info)
set                 -- Changes the state of the targets (use 'help set')
browse              -- Find vessels I can control
genkeys fn [len] [as identity] -- creates new pub / priv keys (default len=1024)
loadkeys fn [as identity]   -- loads filename.publickey and filename.privatekey
list               -- Update and display information about the vessels
upload localfn (remotefn)   -- Upload a file 
download remotefn (localfn) -- Download a file 
delete remotefn             -- Delete a file
reset                  -- Reset the vessel (clear the log and files and stop)
run file [args ...]    -- Shortcut for upload a file and start
start file [args ...] -- Start an experiment
stop               -- Stop an experiment
split resourcefn            -- Split another vessel off of each vessel
join                        -- Join vessels on the same node
help [help | set | show ]    -- help information 
exit                         -- exits the shell
loadstate fn -- Load saved states from a local file. One must call 'loadkeys 
                 username' and 'as username' first before loading the states,
                 so seash knows whose RSA keys to use in deciphering the state
                 file.
savestate fn -- Save the current state information to a local file.
""", 'children':{

  }},


  'show':{'name':'show', 'callback':command_callbacks.show, 'help_text':"""
show info       -- Display general information about the vessels
show users      -- Display the user keys for the vessels
show ownerinfo  -- Display owner information for the vessels
show advertise  -- Display advertisement information about the vessels
show ip [to file] -- Display the ip addresses of the nodes
show hostname   -- Display the hostnames of the nodes
show location   -- Display location information (countries) for the nodes
show coordinates -- Display the latitude & longitude of the nodes
show owner      -- Display a vessel's owner
show targets    -- Display a list of targets
show identities -- Display the known identities
show keys       -- Display the known keys
show log [to file] -- Display the log from the vessel (*)
show files      -- Display a list of files in the vessel (*)
show resources  -- Display the resources / restrictions for the vessel (*)
show offcut     -- Display the offcut resource for the node (*)
show timeout    -- Display the timeout for nodes
show uploadrate -- Display the upload rate which seash uses to estimate
                   the required time for a file upload

(*) No need to update prior, the command contacts the nodes anew
""", 'children':{
      'info':{'name':'info', 'callback':command_callbacks.show_info, 'help_text':'', 'children':{}},
      'users':{'pattern':'users', 'name':'users', 'callback':command_callbacks.show_users, 'help_text':'', 'children':{}},
      'ownerinfo':{'name':'ownerinfo', 'callback':command_callbacks.show_ownerinfo, 'help_text':'', 'children':{}},
      'advertise':{'name':'advertise', 'callback':command_callbacks.show_advertise, 'help_text':'', 'children':{}},
      'ip':{'name':'ip', 'callback':command_callbacks.show_ip, 'help_text':'', 'children':{
          'to':{'name':'to', 'callback':None, 'help_text':'', 'children':{
              '[FILENAME]':{'name':'filename', 'callback':command_callbacks.show_ip_to_file, 'help_text':'', 'children':{}},
          }},
      }},
      'hostname':{'name':'hostname', 'callback':command_callbacks.show_hostname, 'help_text':'', 'children':{}},
      'location':{'name':'location', 'callback':command_callbacks.show_location, 'help_text':'', 'children':{}},
      'coordinates':{'name':'coordinates', 'callback':command_callbacks.show_coordinates, 'help_text':'', 'children':{}},
      'owner':{'name':'owner', 'callback':command_callbacks.show_owner, 'help_text':'', 'children':{}},
      'targets':{'name':'targets', 'callback':command_callbacks.show_targets, 'help_text':'', 'children':{}},
      'identities':{'name':'identities', 'callback':command_callbacks.show_identities, 'help_text':'', 'children':{}},
      'keys':{'name':'keys', 'callback':command_callbacks.show_keys, 'help_text':'', 'children':{}},
      'log':{'name':'log', 'callback':command_callbacks.show_log, 'help_text':'', 'children':{
          'to':{'name':'to', 'callback':None, 'help_text':'', 'children':{
              '[FILENAME]':{'name':'filename', 'callback':command_callbacks.show_log_to_file, 'help_text':'', 'children':{}},
          }},
      }},
      'files':{'name':'files', 'callback':command_callbacks.show_files, 'help_text':'', 'children':{}},
      'resources':{'name':'resources', 'callback':command_callbacks.show_resources, 'help_text':'', 'children':{}},
      'offcut':{'name':'offcut', 'callback':command_callbacks.show_offcut, 'help_text':'', 'children':{}},
      'timeout':{'name':'timeout', 'callback':command_callbacks.show_timeout, 'help_text':'', 'children':{}},
      'uploadrate':{'name':'uploadrate', 'callback':command_callbacks.show_uploadrate, 'help_text':'', 'children':{}},
  }},


  'run':{'name':'run', 'callback':None, 'help_text':'', 'children':{
      '[FILENAME]':{'name':'filename', 'callback':command_callbacks.run_localfn, 'help_text':'','children':{
          '[ARGUMENT]':{'name':'args', 'callback':command_callbacks.run_localfn_arg, 'help_text':'', 'children':{}},
      }},
  }},


  'add':{'name':'add', 'callback':None, 'help_text':'', 'children':{
      '[TARGET]':{'name':'target', 'callback':command_callbacks.add_target, 'help_text':'', 'children':{
          'to':{'name':'to', 'callback':None, 'help_text':'', 'children':{
              '[GROUP]':{'name':'group', 'callback':command_callbacks.add_target_to_group, 'help_text':'', 'children':{}},
          }},
      }},
      'to':{'name':'to', 'callback':None, 'help_text':'', 'children':{
          '[GROUP]':{'name':'group', 'callback':command_callbacks.add_to_group, 'help_text':'', 'children':{}},
      }},
  }},


  'move':{'name':'move', 'callback':None, 'help_text':'', 'children':{
      '[TARGET]':{'name':'target', 'callback':None, 'help_text':'', 'children':{
          'to':{'name':'to', 'callback':None, 'help_text':'', 'children':{
              '[GROUP]':{'name':'group', 'callback':command_callbacks.move_target_to_group, 'help_text':'', 'children':{}},
          }},
      }},
  }},


  'remove':{'name':'remove', 'callback':None, 'help_text':'', 'children':{
      '[TARGET]':{'name':'target', 'callback':command_callbacks.remove_target, 'help_text':'', 'children':{
          'from':{'name':'from', 'callback':None, 'help_text':'', 'children':{
              '[GROUP]':{'name':'group', 'callback':command_callbacks.remove_target_from_group, 'help_text':'', 'children':{}},
          }},
      }},
      'from':{'name':'from', 'callback':None, 'help_text':'', 'children':{
          '[GROUP]':{'name':'group', 'callback':command_callbacks.remove_from_group, 'help_text':'', 'children':{}},
      }},
  }},


  'set':{'name':'set', 'callback':command_callbacks.set, 'help_text':"""
set users [ identity ... ]  -- Change a vessel's users
set ownerinfo [ data ... ]    -- Change owner information for the vessels
set advertise [ on | off ] -- Change advertisement of vessels
set owner identity        -- Change a vessel's owner
set timeout count  -- Sets the time that seash is willing to wait on a node
set uploadrate speed -- Sets the upload rate which seash will use to estimate
                        the time needed for a file to be uploaded to a vessel.
                        The estimated time would be set as the temporary 
                        timeout count during actual process. Speed should be 
                        in bytes/sec.
set autosave [ on | off ] -- Sets whether to save the state after every command.
                             Set to 'off' by default. The state is saved to a
                             file called 'autosave_keyname', where keyname is 
                             the name of the current key you're using.
""", 'children':{
      'users':{'name':'users', 'callback':None, 'help_text':'', 'children':{
          '[ARGUMENT]':{'name':'args', 'callback':command_callbacks.set_users_arg, 'help_text':'', 'children':{}},
      }},
      'ownerinfo':{'name':'ownerinfo', 'callback':None, 'help_text':'', 'children':{
          '[ARGUMENT]':{'name':'args', 'callback':command_callbacks.set_ownerinfo_arg, 'help_text':'', 'children':{}},
      }},
      'advertise':{'name':'advertise', 'callback':None, 'help_text':'', 'children':{
          '[ARGUMENT]':{'name':'args', 'callback':command_callbacks.set_advertise_arg, 'help_text':'', 'children':{}},
      }},
      'owner':{'name':'owner', 'callback':None, 'help_text':'', 'children':{
          '[ARGUMENT]':{'name':'args', 'callback':command_callbacks.set_owner_arg, 'help_text':'', 'children':{}},
      }},
      'timeout':{'name':'timeout', 'callback':None, 'help_text':'', 'children':{
          '[ARGUMENT]':{'name':'args', 'callback':command_callbacks.set_timeout_arg, 'help_text':'', 'children':{}},
      }},
      'uploadrate':{'name':'uploadrate', 'callback':None, 'help_text':'', 'children':{
          '[ARGUMENT]':{'name':'args', 'callback':command_callbacks.set_uploadrate_arg, 'help_text':'', 'children':{}},
      }},
      'autosave':{'name':'autosave', 'callback':None, 'help_text':'', 'children':{
          '[ARGUMENT]':{'name':'args', 'callback':command_callbacks.set_autosave_arg, 'help_text':'', 'children':{}},
      }},
  }},


  'browse':{'name':'browse', 'callback':command_callbacks.browse, 'help_text':'', 'children':{
      '[ARGUMENT]':{'name':'args', 'callback':command_callbacks.browse_arg, 'help_text':'', 'children':{}},
  }},


  'genkeys':{'name':'genkeys', 'callback':None, 'help_text':'', 'children':{
      '[FILENAME]':{'name':'filename', 'callback':command_callbacks.genkeys_filename, 'help_text':'', 'children':{
          '[ARGUMENT]':{'name':'args', 'callback':command_callbacks.genkeys_filename_len, 'help_text':'', 'children':{
              'as':{'name':'as', 'callback':None, 'help_text':'', 'children':{
                  '[ARGUMENT]':{'name':'keyname', 'callback':command_callbacks.genkeys_filename_len_as_identity, 'help_text':'', 'children':{}},
              }},
          }},
          'as':{'name':'as', 'callback':None, 'help_text':'', 'children':{
              '[ARGUMENT]':{'name':'keyname', 'callback':command_callbacks.genkeys_filename_as_identity, 'help_text':'', 'children':{}},
          }},
      }},
  }},


  'loadkeys':{'name':'loadkeys', 'callback':None, 'help_text':'', 'children':{
      '[FILENAME]':{'name':'filename', 'callback':command_callbacks.loadkeys_keyname, 'help_text':'', 'children':{
          'as':{'name':'as', 'callback':None, 'help_text':'', 'children':{
              '[ARGUMENT]':{'name':'args', 'callback':command_callbacks.loadkeys_keyname_as, 'help_text':'', 'children':{}},
          }},
      }},
  }},


  'loadpub':{'name':'loadpub', 'callback':None, 'help_text':'', 'children':{
      '[FILENAME]':{'name':'filename', 'callback':command_callbacks.loadpub_filename, 'help_text':'', 'children':{
          'as':{'name':'as', 'callback':None, 'help_text':'', 'children':{
              '[ARGUMENT]':{'name':'args', 'callback':command_callbacks.loadpub_filename_as, 'help_text':'', 'children':{}},
          }},
      }},
  }},


  'loadpriv':{'name':'loadpriv', 'callback':None, 'help_text':'', 'children':{
      '[FILENAME]':{'name':'filename', 'callback':command_callbacks.loadpriv_filename, 'help_text':'', 'children':{
          'as':{'name':'as', 'callback':None, 'help_text':'', 'children':{
              '[ARGUMENT]':{'name':'args', 'callback':command_callbacks.loadpriv_filename_as, 'help_text':'', 'children':{}},
          }},
      }},
  }},

  
  'list':{'name':'list', 'callback':command_callbacks.list, 'help_text':'', 'children':{}},


  'upload':{'name':'upload', 'callback':None, 'help_text':'', 'children':{
      '[FILENAME]':{'name':'filename', 'callback':command_callbacks.upload_filename, 'help_text':'', 'children':{
          '[ARGUMENT]':{'name':'args', 'callback':command_callbacks.upload_filename_remotefn, 'help_text':'', 'children':{}}
      }},
  }},


  'download':{'name':'download', 'callback':None, 'help_text':'', 'children':{
      '[FILENAME]':{'name':'filename', 'callback':command_callbacks.download_filename, 'help_text':'', 'children':{
          '[ARGUMENT]':{'name':'args', 'callback':command_callbacks.download_filename_localfn, 'help_text':'', 'children':{}}
      }},
  }},


  'delete':{'name':'delete', 'callback':None, 'help_text':'', 'children':{
      '[FILENAME]':{'name':'filename', 'callback':command_callbacks.delete_remotefn, 'help_text':'', 'children':{}},
  }},


  'reset':{'name':'reset', 'callback':command_callbacks.reset, 'help_text':'', 'children':{}},


  'start':{'name':'start', 'callback':None, 'help_text':'', 'children':{
      '[FILENAME]':{'name':'filename', 'callback':command_callbacks.start_remotefn, 'help_text':'', 'children':{
          '[ARGUMENT]':{'name':'args', 'callback':command_callbacks.start_remotefn_arg, 'help_text':'', 'children':{}},
      }},
  }},


  'stop':{'name':'stop', 'callback':command_callbacks.stop, 'help_text':'', 'children':{}},


  'split':{'name':'split', 'callback':None, 'help_text':'', 'children':{
      '[FILENAME]':{'name':'filename', 'callback':command_callbacks.split_resourcefn, 'help_text':'', 'children':{}},
  }},


  'join':{'name':'join', 'callback':command_callbacks.join, 'help_text':'', 'children':{}},


  'exit':{'name':'exit', 'callback':command_callbacks.exit, 'help_text':'', 'children':{}},


  'loadstate':{'name':'loadstate', 'callback':None, 'help_text':'', 'children':{
      '[FILENAME]':{'name':'filename', 'callback':command_callbacks.loadstate_filename, 'help_text':'', 'children':{}},
  }},


  'savestate':{'name':'savestate', 'callback':None, 'help_text':'', 'children':{
      '[FILENAME]':{'name':'filename', 'callback':command_callbacks.savestate_filename, 'help_text':'', 'children':{}},
  }},


  'update':{'name':'update', 'callback':command_callbacks.update, 'help_text':'', 'children':{}},


  'contact':{'name':'contact', 'callback':None, 'help_text':'', 'children':{
      '[ARGUMENT]':{'name':'args', 'callback':command_callbacks.contact, 'help_text':'', 'children':{}},
  }},

}




##### All methods that adds to the seash command dictionary #####


# Creates a deep copy of the seash dictionary while avoiding any of the 
# commands in the passed list.
# Only works in the first level of the dictionary. Will not search for the 
# existence of the avoided command in deeper levels of the dictionary.
def _deep_copy_main_dict(avoided_cmds_list):

  command_dict_copy = seashcommanddict.copy()

  # For every command pattern found in the passed list,
  # the function will delete it from
  for cmd in avoided_cmds_list:

    if cmd in command_dict_copy:

      del command_dict_copy[cmd]
  

  return command_dict_copy




# Returns a copy of a command's dictionary with an empty dictionary for its children
def _shallow_copy(cmd_dict):
  cmd_dict_copy = cmd_dict.copy()
  cmd_dict_copy['children'] = {}
  return cmd_dict_copy





# Returns the seash command dictionary after making any necessary additions to it

def return_command_dictionary():
  
  # Sets the entire seash command dictionary as 'on target' children except itself
  seashcommanddict['on']['children']['[TARGET]']['children'] = _deep_copy_main_dict(['on'])
  
  # Sets the entire seash command dictionary as 'as keyname' children except itself
  seashcommanddict['as']['children']['[KEYNAME]']['children'] = _deep_copy_main_dict(['as'])

  # Sets the entire seash command dictionary as 'help' children except itself
  seashcommanddict['help']['children'] = _deep_copy_main_dict(['help'])

  return seashcommanddict





##### User input parsing related methods #####

"""
seash's command parser:
The parser receives the string of commands the user inputted and proceeds
to iterate through seashcommanddict to verify that the each of the command
string corresponds to a key of seash's command dictionary, and each subsequent 
string corresponds to a command key of the current command dictionary's 
dictionary of children. 

At the same time, a sub-dictionary of seashcommanddict is being built that holds 
only the chain of dictionaries that corresponds to the user's input, with the only
difference being that any user-inputted argument will replace the command key of the 
command dictionary associated with it. Thus, instead of '[TARGET]', the key to the 
command dictionary would instead be '%1'. 

Targets and Group name arguments will be checked to see if the name specified
actually exists, and general Argument command dictionaries with no children will
have the corresponding user input string and any string that follows be spliced
into a single string with spaces in between each word.

A ParseError will be raised if the argument given for Target or Group does not
exist, and also if the user inputted command word does not correspond to any of the
command keys of the current dictionaries of dictionaries the iterator is looking
at and there are no argument keys to suggest the inputted word is an user argument.
"""
def parse_command(userinput):

  userinput = userinput.strip()

  userstringlist = userinput.split()


  # Dictionary of dictionaries that gets built corresponding to user input
  input_dict = {}
  # Iterator that builds the input_dict
  input_dict_builder = input_dict

  # The iterator that runs through the command dictionary
  seash_dict_mark = return_command_dictionary()


  # Cycles through the user's input string by string
  for user_string in userstringlist:

    # First, an initial check to see if user's input matches a specified command word
    for cmd_pattern in seash_dict_mark.iterkeys():

      if user_string == cmd_pattern:

        # Appends a copy to avoid changing the master list of dictionaries
        input_dict_builder[cmd_pattern] = _shallow_copy(seash_dict_mark[cmd_pattern])

        # Moves the input dictionary builder into the next empty children dictionary
        input_dict_builder = input_dict_builder[cmd_pattern]['children']

        # Iterates into the children dictionary of the next level of command that may follow
        seash_dict_mark = seash_dict_mark[cmd_pattern]['children']

        break


    # If the user's input string does not match the any of the command pattern directly,
    # looks through the command's children for the possibility of being an
    # user inputed argument, generally denoted by starting with a '['
    else:
      for cmd_pattern in seash_dict_mark.iterkeys():

        # Checks if the input is listed as a valid target, and appends
        # the command dictionary to the input_dict
        if cmd_pattern.startswith('['):
          if cmd_pattern == '[TARGET]' or cmd_pattern == '[GROUP]':
            
            # Compares input with current list of targets and/or groups
            # Raise exception if not found in list of targets
            if user_string not in seash_global_variables.targets:
              raise seash_exceptions.ParseError("Target does not exist")

            # Distinguish between general targets and specific groups if looking for
            # a group. Raises an error if user's input is not a valid group name
            elif cmd_pattern == '[GROUP]' and user_string.startswith('%'):
              raise seash_exceptions.ParseError("Invalid group name")
          
          # Necessity of checking existence of keynames yet to be determined
          #elif cmd_pattern == '[KEYNAME]':
          #  pass

          # Necessity of verifying existence of file yet to be determined
          #elif cmd_pattern == '[FILENAME]':
          #  pass
          
          # simply appends to input_dict
          elif cmd_pattern == '[ARGUMENT]':

            # If ARGUMENT doesn't have any children, joins the rest of the user's input
            # into a single string
            if not seash_dict_mark[cmd_pattern]['children']:
              arg_string = " ".join(userstringlist[userstringlist.index(user_string):])
              for string in userstringlist[userstringlist.index(user_string):]:
                userstringlist.remove(string)

              # Resets the user_string as arg_string for consistency in rest of code
              user_string = arg_string
              userstringlist.append(user_string)
  

          # Appends a copy of the dictionary to avoid changing the master list of command dictionaries
          # Also sets the name of the target specified by the user as the key of the command's dictionary
          # for later use by the command's callback
          input_dict_builder[user_string] = _shallow_copy(seash_dict_mark[cmd_pattern])
          
          # Sets itself as the recently-added command dictionary's children to be ready to
          # assign the next command dictionary associated with the next user's input string
          input_dict_builder = input_dict_builder[user_string]['children']
            
          # sets the next list of command dictionaries
          seash_dict_mark = seash_dict_mark[cmd_pattern]['children']

          break



      # If the user input doesn't match any of the pattern words and there's no
      # pattern that suggest it may be a user input argument, raise an exception
      # for going outside of seash's command dictionary
      else:
        raise seash_exceptions.ParseError("Command not understood")



  return input_dict



"""
seash's command dispatcher:
Taking in the input dictionary of dictionaries, input_dict, the dispatcher iterates
through the series of dictionaries and executes the command callback function of
any command dictionaries that has the key 'priority' while keeping reference of the
last callback function of the command dictionary that had one. After completing
the iteration, if the referenced command callback function has not been executed
already from priority status, the dispatcher proceeds to executes the function. 

Each callback function will be passed a copy of the input_dict for access to 
user-inputted arguments and the environment_dict that keeps track of the current 
state of seash.

A DispatchError will be raised if at the end of the iteration there are no valid command
callbacks to be executed.
"""
def command_dispatch(input_dict, environment_dict):
  
  # Iterator through the user command dictionary
  dict_mark = input_dict


  # Sets the command callback method to be executed
  current_callback = None

  
  # Sets the last 'interrupt' command's callback method that was executed.
  # Used to avoid having current_callback execute the same command function again
  interrupt_callback = None


  # First, general check for any command dictionaries with the 'priority' key
  # Execute the callback methods of those commands
  
  while dict_mark.keys():


    # Pulls out the command word, which also serves as the key to the command's dictionary
    # It should be the only key in the key list of the children's dictionary
    command_key = dict_mark.keys()[0]


    # Sets the callback method reference if command's 'callback' isn't set to None
    if dict_mark[command_key]['callback'] is not None:
      current_callback = dict_mark[command_key]['callback']


    # Executes the callback method of all commands that contains the 'priority' key
    if 'priority' in dict_mark[command_key]:
      interrupt_callback = dict_mark[command_key]['callback']
      interrupt_callback(input_dict.copy(), environment_dict)

      # In the case of 'help', breaks out of the dispatch loop to avoid executing any other
      # command's function
      if command_key == 'help':
        break


    # Iterates into the next dictionary of children commands
    dict_mark = dict_mark[command_key]['children']



  # Raises an exception if current_callback is still None
  if current_callback is None:
    raise seash_exceptions.DispatchError("Invalid command. Please check that the command has been inputted correctly.")


  # Executes current_callback's method if it's not the same one as interrupt_callback
  elif not interrupt_callback == current_callback:
    current_callback(input_dict.copy(), environment_dict)
