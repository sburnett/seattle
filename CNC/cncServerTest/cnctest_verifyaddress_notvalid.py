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
import socket
from repyportability import *
import cnctestlib

def main():
  if len(sys.argv) < 3:
    print "invalid number of agruments"
    return
  
  ip = sys.argv[1]
  port = int(sys.argv[2])


  #we will need the update key range and query tables
  sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  sock.sendto("GetUserKeyRangeTables", (ip, port))
  message = sock.recv(1024)
  parsed_data = message.split()
  
  if parsed_data[0]!="GetUserKeyRangeTablesReply":
    print "invallid reply type received: "+ message
    return
    
  update_key_range_table = cnctestlib.parse_update_key_ranges_string(parsed_data[1])
  query_server_table = cnctestlib.parse_query_table_string(parsed_data[2])
  
  

  #first register two users
  handle = openconn(ip, port)
  handle.send('RegisterAddressRequest testidv01,testidv02')
  reply = handle.recv(1024)
  stopcomm(handle)
  
  parsed_reply = reply.split()
  
  if (parsed_reply[0]!="RegisterAddressRequestComplete") :
    print ("Registration failed, reply from server = " + reply)
    return
    
  #wait a short time for the update server to receive the forwarded registration request
  sleep(2)
  
  #get the address of the update or query server for the userkey testidv02
  server_addresses = cnctestlib.get_addresses_for_userkey("testidv02", update_key_range_table, query_server_table)
  
  #for this test, we will only check one of the addresses
  target_server_address = server_addresses[0]
  
  #send a udp packet requesting to verify the address for the users and check the reply
  sock.sendto("VerifyAddressRequest bogususer1,bogususer3,bogususer4 "+getmyip(), (target_server_address[0], target_server_address[1]))
  message = sock.recv(1024)
  
  parsed_data = message.split()
  
  if parsed_data[0]!="VerifyAddressReply":
    print "invallid reply type received: "+ message
    return
  elif parsed_data[1] != getmyip():
    print "data returned for incorrect address: " + message
    return
  elif parsed_data[3] != "False" : 
    print "non-existent address found valid by server: " + message
    return
    
  print "done"

if __name__ == "__main__":
  main()