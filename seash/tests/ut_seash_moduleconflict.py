"""
Test the detection of conflicting commanddicts.

"""

import seash_modules

def nullfunction():
  pass

cmddict = {
  'hello':{'callback': nullfunction, 'help_text': '', 'summary': '', 'children':{}},
}

# These should not error out
seash_modules.ensure_no_conflicts_in_commanddicts(cmddict, {})
seash_modules.ensure_no_conflicts_in_commanddicts({}, cmddict)

noshared_cmddict = {
  'hello2':{'callback': nullfunction, 'help_text': '', 'summary': '', 'children':{}},
}
seash_modules.ensure_no_conflicts_in_commanddicts(cmddict, noshared_cmddict)
seash_modules.ensure_no_conflicts_in_commanddicts(noshared_cmddict, cmddict)

onlyonedefined_cmddict = {
  'hello':{'callback': None, 'help_text': '', 'summary': '', 'children':{}},
}

seash_modules.ensure_no_conflicts_in_commanddicts(cmddict, onlyonedefined_cmddict)
seash_modules.ensure_no_conflicts_in_commanddicts(onlyonedefined_cmddict, cmddict)

bothdefined_noconflict_cmddict = {
  'hello':{'callback': nullfunction, 'help_text': '', 'summary': '', 'children':{
    'hello2': {'callback': nullfunction, 'help_text': '', 'summary': '', 'children':{}
    }}},
}

seash_modules.ensure_no_conflicts_in_commanddicts(cmddict, bothdefined_noconflict_cmddict)
seash_modules.ensure_no_conflicts_in_commanddicts(bothdefined_noconflict_cmddict, cmddict)

