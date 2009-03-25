# Testing acquiring from Node Manager...
import nm_remote_api
import sys

# Our nodes to run on
hosts = ['128.208.1.161', '128.208.1.240', '128.208.1.169', '128.208.1.108', '128.208.1.166']
filename = 'forwarder_rpc.py'

def usage():
  print "Usage: python natd.py <status | start | stop | restart>"
  sys.exit(1)

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
