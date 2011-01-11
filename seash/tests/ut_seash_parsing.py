"""
Passes a series of commands to the parser in seash_dictionary and make sures
the parser returns the correct input dictionary.

Make sure to update this if the following command's dictionaries changes:
browse
show ownerinfo
set autosave
upload
"""
import seash_dictionary
import command_callbacks


resulting_dictionary = seash_dictionary.parse_command("browse")

expected_dictionary = {'browse':{'name':'browse', 'callback':command_callbacks.browse, 'help_text':"""
browse [advertisetype]

This command will use the default identity to search for vessels that can
be controlled.   Any vessel with the advertise flag set will be advertised
in at least one advertise service.   browse will look into these services
and add any vessels it can contact.

Setting advertisetype will restrict the advertise lookup to only use that 
service.   Some permitted values for advertisetype are central, DHT, and DOR.

Example:
exampleuser@ !> show targets
%all (empty)
exampleuser@ !> browse
['192.x.x.2:1224', '193.x.x.42:1224', '219.x.x.62:1224']
Added targets: %2(193.x.x.42:1224:v18), %3(219.x.x.62:1224:v4), %1(192.x.x.2:1224:v3)
Added group 'browsegood' with 3 targets
exampleuser@ !> show targets
browsegood ['192.x.x.2:1224:v3', '193.x.x.42:1224:v18', '219.x.x.62:1224:v4']
%3 ['219.x.x.62:1224:v4']
%all ['192.x.x.2:1224:v3', '193.x.x.42:1224:v18', '219.x.x.62:1224:v4']
%1 ['192.x.x.2:1224:v3']
%2 ['193.x.x.42:1224:v18']

""", 'children':{}}}

if not resulting_dictionary == expected_dictionary:
  print "Incorrect values in command dictionary returned from parser: browse"




resulting_dictionary = seash_dictionary.parse_command("show ownerinfo")

expected_dictionary = {'show':{'name':'show', 'callback':command_callbacks.show, 'help_text':"""
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
    'ownerinfo':{'name':'ownerinfo', 'callback':command_callbacks.show_ownerinfo, 'help_text':"""
show ownerinfo

This lists the ownerinfo strings for vessels in the default group.   See
'set ownerinfo' for more details
""", 'children':{}}}}}

if not resulting_dictionary == expected_dictionary:
  print "Incorrect values in command dictionary returned from parser: show ownerinfo"




resulting_dictionary = seash_dictionary.parse_command("set autosave off")

expected_dictionary = {'set':{'name':'set', 'callback':command_callbacks.set, 'help_text':"""
Commands requiring owner credentials on a vessel:
set users [ identity ... ]  -- Change a vessel's users
set ownerinfo [ data ... ]    -- Change owner information for the vessels
set advertise [ on | off ] -- Change advertisement of vessels
set owner identity        -- Change a vessel's owner

Shell settings:
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
      'autosave':{'name':'autosave', 'callback':None, 'help_text':"""
set autosave [on/off]

When turned on, the shell settings such as keys, targets, timeout value, etc.
will all be persisted to disk after every operation.   These are saved in a
file called 'autosave_(user's keyname)', which is encrypted with the default identity.   The user
can then restore the shell's state by typing 'loadstate identity'.

Example:
exampleuser@%1 !> set autosave on
exampleuser@%1 !> exit
(restart seash.py)
 !> loadkeys exampleuser
 !> as exampleuser
exampleuser@ !> loadstate autosave_exampleuser
exampleuser@%1 !>

""", 'children':{
          'off':{'name':'args', 'callback':command_callbacks.set_autosave_arg, 'help_text':'', 'children':{}},
      }},
  }}}

if not resulting_dictionary == expected_dictionary:
  print "Incorrect values in command dictionary returned from parser for command: set autosave off"



resulting_dictionary = seash_dictionary.parse_command("upload files.txt")

expected_dictionary = {'upload':{'name':'upload', 'callback':None, 'help_text':"""
upload srcfilename [destfilename]

Uploads a file into all vessels in the default group.   The file name that is
created in those vessels is destfilename (or srcfilename by default).

Example:
exampleuser@%1 !> show files
Files on '192.x.x.2:1224:v3': ''
exampleuser@%1 !> upload example.1.1.repy
exampleuser@%1 !> show files
Files on '192.x.x.2:1224:v3': 'example.1.1.repy'

""", 'children':{
      'files.txt':{'name':'filename', 'callback':command_callbacks.upload_filename, 'help_text':'', 'children':{}}}}}

if not resulting_dictionary == expected_dictionary:
  print "Incorrect values in command dictionary returned from parser: upload files.txt"




resulting_dictionary = seash_dictionary.parse_command("upload files.txt apples and oranges")

expected_dictionary = {'upload':{'name':'upload', 'callback':None, 'help_text':"""
upload srcfilename [destfilename]

Uploads a file into all vessels in the default group.   The file name that is
created in those vessels is destfilename (or srcfilename by default).

Example:
exampleuser@%1 !> show files
Files on '192.x.x.2:1224:v3': ''
exampleuser@%1 !> upload example.1.1.repy
exampleuser@%1 !> show files
Files on '192.x.x.2:1224:v3': 'example.1.1.repy'

""", 'children':{
      'files.txt':{'name':'filename', 'callback':command_callbacks.upload_filename, 'help_text':'', 'children':{
          'apples and oranges':{'name':'args', 'callback':command_callbacks.upload_filename_remotefn, 'help_text':'', 'children':{}}
      }},
  }}}

if not resulting_dictionary == expected_dictionary:
  print "Incorrect values in command dictionary returned from parser: upload files.txt apples and oranges"
