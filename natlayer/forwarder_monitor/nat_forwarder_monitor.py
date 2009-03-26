"""
  <Purpose>
    Deploy/manage/monitor forwarder daemons on seattle vessels.
"""
import nm_remote_api
import sys

# i want to change the way the nm_remote_api module works a little
# without editing the actual file in case I'd mess somebody else up
# but I don't want to duplicate nm_remote_api
def infinitely_run_target(longname, filename, filedata, argstring, timeout=240):
    # smart argstring check:
    if filename.find("/") != -1:
        error_msg = "Please pass in the filename without any directory/hierarchy information (passed in '%s')" % filename
        return (False, error_msg)

    argparts = argstring.partition(" ")
    if argparts[0] != filename:
        # attempt to fix
        if argparts[2] != "":
            argstring = filename + " " + argparts[2].strip()
        else:
            argstring = filename

    nm_remote_api.check_is_initialized()

    vesselname = nm_remote_api.vesselinfo[longname]['vesselname']
    try:
        nm_remote_api.nmclient_signedsay(nm_remote_api.vesselinfo[longname]['handle'], "AddFileToVessel", 
                           vesselname, filename, filedata)
    except nm_remote_api.NMClientException, e:
        return (False, str(e))
    
    #print "Successfully added ", filename, " to vessel"
    
    try:
        nm_remote_api.nmclient_signedsay(nm_remote_api.vesselinfo[longname]['handle'], "StartVessel", 
                           vesselname, argstring)
    except nm_remote_api.NMClientException, e:
        return (False, str(e))
    
    return (True, "No checking for termination")

# override function
nm_remote_api.run_target = infinitely_run_target # small change to nm_remote_api

#########
# Setup
########

# Our nodes to run on
#hosts = ['128.208.1.161', '128.208.1.240', '128.208.1.169', '128.208.1.108', '128.208.1.166']
hosts = ['128.112.139.75', '128.112.139.108', '128.112.139.80', '128.112.139.97', '128.112.139.2']
filename = 'forwarder_rpc.py' # code to run on them

def usage():
  print "Usage: python natd.py <status | start | stop | restart>"
  sys.exit(1)

#############
# Start of Main
###########
# must give exactly one argument
if len(sys.argv) != 2:
  usage()

# acquire the vessels
print "Acquiring vessels..."
success, info = nm_remote_api.initialize(hosts, 'jordanr')
if not success:
  print "Could not acquire hosts"
  sys.exit(2)
print

# everything is ready to go
# what was the arg?
cmd = sys.argv.pop()

if cmd == 'status':
  print "Checking the status of vessels..."
  for lname in info:
    nm_remote_api.is_vessel_finished(lname)
elif cmd == 'start':
  print "Starting " + str(filename) + " on all vessels..."
  FILE = open(filename)
  filedata = FILE.read()
  FILE.close()
  argstring = filename
  dic = nm_remote_api.run_on_targets(info, filename, filedata, argstring, 10)
  print dic
elif cmd == 'stop':
  print "Stopping " + str(filename) + " on all vessels..."
  for longname in info:
    nm_remote_api.stop_target(longname)

else:
  usage()


# success
sys.exit(0)
