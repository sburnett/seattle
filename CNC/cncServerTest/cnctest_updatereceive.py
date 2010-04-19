"""
#########IMPORTANT USE INFORMATION#########:
SERVER MUST BE RESTARTED EACH TIME BEFORE THIS TEST IS RUN OR IT WILL FAIL.
ALTERNATIVELY, WAIT UNTIL THE REGISTRATION DATA FROM THE PREVIOUS TEST RUN EXPIRES BEFORE RERUNNING THE TEST.

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




def main():
  if len(sys.argv) < 3:
    print "invalid number of agruments"
    return
  
  ip = sys.argv[1]
  port = int(sys.argv[2])
  
  local_ip=getmyip()
  local_register_port = 50019
  
  #first register two users
  handle = openconn(ip, port, local_ip, local_register_port)
  handle.send('RegisterAddressRequest testidvr02')
  reply = handle.recv(1024)
  stopcomm(handle)
  
  parsed_reply = reply.split()
  
  if (parsed_reply[0]!="RegisterAddressRequestComplete") :
    print ("Registration failed, reply from server = " + reply)
    return
    
  #wait to receive an update packet
  sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  sock.bind((local_ip, local_register_port))
  message = sock.recv(1024)
  sock.close()
  
  parsed_data = message.split()
  
  #if this is not the update we want, keep waiting untill we receive it
  while (parsed_data[0]!="AddressListUpdate" and parsed_data[1] != "testidvr02"):
    message = sock.recv(1024)
    parsed_data = message.split()
    
  address_data = parsed_data[2].split(':')
  if address_data[0] != local_ip: 
    print "incorrect added list data: " + message
    return
  elif int(address_data[1]) != local_register_port: 
    print "incorrect added list data: " + message
    return
  elif parsed_data[3] != "None":
    print "incorrect deleted list data: " + message
  
  
  print "done"

if __name__ == "__main__":
  main()