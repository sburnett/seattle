"""
<Author>
  Cosmin Barsan
  
<Expected Output>
  The test will pring "done" if successfull

<Purpose>
  Sends a single registration request to the server at specified port and ip, and verifies the reply received
  
<Usage>
 python <test_name> <ip_address> <port number>
  
"""

import sys
from repyportability import *

def main():
  if len(sys.argv) < 3:
    print "invalid number of agruments"
    return
  
  ip = sys.argv[1]
  port = int(sys.argv[2])

  handle = openconn(ip, port)
  handle.send('RegisterAddressRequest testid1,testid2,testid3')
  reply = handle.recv(1024)
  
  stopcomm(handle)
  
  parsed_reply = reply.split()
  
  if (parsed_reply[0]=="RegisterAddressRequestComplete") :
    print "done"
  else:
    print ("Registration failed, reply from server = " + reply)
    

if __name__ == "__main__":
  main()