"""
<Author>
  Cosmin Barsan
  
<Expected Output>
  The test will pring "done" if successfull

<Purpose>
  Sends a single GetUserKeyRangeTable request to the server at specified port and ip, and verifies the reply received
  
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

  #send a udp packet requesting the address list for the users and check the reply
  #a socket object is used because it is simpler to get the message reply
  sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  sock.sendto("GetUserKeyRangeTables", (ip, port))
  message = sock.recv(1024)
  
  parsed_data = message.split()
  
  if parsed_data[0]!="GetUserKeyRangeTablesReply":
    print "invallid reply type received: "+ message
    return
  elif parsed_data[1] == "None":
    print "Registration server returned no update server entries in GetUserKeyRangeTablesReply: " + message
    return
    
  print "done"
  return
  
if __name__ == "__main__":
  main()