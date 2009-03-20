# Testing from GENI...
#
#import time
#import socket
#report = ("No response", "Alive")
# hosts = ['128.208.1.150', '128.208.1.163', '128.208.1.179', '128.208.1.232']
#PORT = 63111  # my GENIport
#print time.ctime()
#for ip in hosts:
#  print "Testing ",ip,
#  try: 
#    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#    s.connect((ip, PORT))
#    s.close()
#    print "Alive"
#  except:
#    print "Dead"
#  time.sleep(1)
#print time.ctime()


# Testing acquiring from Node Manager...
import nm_remote_api

hosts = ['128.208.1.179', '128.208.1.116', '128.208.1.108', '128.208.1.150', '128.208.1.163']
success, info = nm_remote_api.initialize(hosts, 'jordanr')

print success
print info


# Test running a file...
#
#filename='test.repy'
#FILE = open(filename)
#filedata= FILE.read()
#FILE.close()
#argstring = filename
# dic = nm_remote_api.run_on_targets(info, filename, filedata, argstring)
# print dic


# Test checking on status...
for lname in info:
  nm_remote_api.is_vessel_finished(lname)
