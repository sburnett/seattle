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
  handle.send('RegisterAddressRequest testid11,testid12')
  reply = handle.recv(1024)
  stopcomm(handle)
  
  parsed_reply = reply.split()
  
  if (parsed_reply[0]!="RegisterAddressRequestComplete") :
    print ("Registration failed, reply from server = " + reply)
    return
  
  #save the renew key from the registration
  renew_key = parsed_reply[1]
  
  #wait a short time for the update server to receive the forwarded registration request
  sleep(2)

  #get the address of the update or query server for the userkey testid12
  server_addresses = cnctestlib.get_addresses_for_userkey("testid12", update_key_range_table, query_server_table)
  
  #for this test, we will only check one of the addresses
  target_server_address = server_addresses[0]
  
  
  #send a udp packet requesting the address list for the users and check the reply
  sock.sendto("GetAddressesForUserRequest testid12", (target_server_address[0], target_server_address[1]))
  message = sock.recv(1024)
  
  parsed_data = message.split()
  
  if parsed_data[0]!="GetAddressesReply":
    print "invallid reply type received: "+ message
    return
  elif len(parsed_data) < 3:
    print "no addresses found for user key: " + message
    return
  
  #store timestamp returned with the address in the address list
  address_timestamp = (parsed_data[2].split(':'))[2] 
  address_timestamp = float(address_timestamp)
  
  #sleep for about 3 second so we can see a difference in the timestamps later
  sleep(3)
  
  
  #send a renew registration request using the renew key
  sock.sendto("RenewAddressRequest testid13,testid11,testid12 " + renew_key, (ip, port))
  message = sock.recv(1024)
  
  #ignore the update packet if it arrives before teh reply
  if (message.split()[0]=="AddressListUpdate"):
    message = sock.recv(1024)
  
  if message != "RenewAddressRequestComplete" : 
    print "failed to renew address: "+ message
    return
  
  #wait a short time for the update server to receive the forwarded registration request
  sleep(2)
  
  #request the address list again for user testid12 and compare the timestamps to see if they have been updated
  sock.sendto("GetAddressesForUserRequest testid12", (target_server_address[0], target_server_address[1]))
  message = sock.recv(1024)
  sock.close()
  
  parsed_data = message.split()
    
  if parsed_data[0]!="GetAddressesReply":
    print "invallid reply type received: "+ message
    return
  elif len(parsed_data) < 3:
    print "no addresses found for user key: " + message
    return
    
  #store timestamp returned with the address in the address list
  new_address_timestamp = (parsed_data[2].split(':'))[2] 
  new_address_timestamp = float(new_address_timestamp)
  
  diff = (new_address_timestamp - address_timestamp)
  if diff < 2.9:
    print "timestamp was not correctly updated by renew address, expected 3 sec difference, actual difference was: " + str(diff)
    return
    
  
  print "done"

if __name__ == "__main__":
  main()