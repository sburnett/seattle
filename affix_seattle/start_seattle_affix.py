from repyportability import *
_context = locals()
add_dy_support(_context)

dy_import_module_symbols("advertise.repy")

try:
    advertise_announce("SeattleAffixStack", "(NoopShim)", 600)
except AdvertiseError, e:
    print "Advertise error: " + str(e)

lookup_string = advertise_lookup("SeattleAffixStack")
print "Current lookup string is: " + str(lookup_string)

try:
    advertise_announce("EnableSeattleAffix", "True", 600)
except AdvertiseError, e:
    print "Advertise error: " + str(e)


lookup_string = advertise_lookup("EnableSeattleAffix")
print "EnableSeattleAffix flag set to: " + str(lookup_string)
