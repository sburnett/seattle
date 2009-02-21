"""
<Program Name> 
  BandwidthClient.py

<Started>
  Feb 2 2009

<Authors> 
  Anthony Honsta 
  Carter Butaud
  
"""
# get_mess will build a string of 0's
def get_mess(bytes):
  mess = ""
  for i in range(bytes):
    mess += "0"
  return mess
    
if callfunc == "initialize":
  ip = getmyip()
  mycontext["tcp_port"] = 12345
  mycontext["udp_port"] = 12346
  mycontext["server_ip"] = "128.208.1.137"

  num_to_send = 30 # number of packets to be sent
  
  # Open a tcp connection to the server
  server_conn = openconn(mycontext["server_ip"], mycontext["tcp_port"])
  server_conn.send(str(num_to_send))
  server_conn.close()
    
  # Send the UDP packet train
  for i in range(num_to_send):
    sendmess(mycontext["server_ip"], mycontext["udp_port"], get_mess(512))
 
  sleep(1)
  
  # Open the final tcp connection with the server to
  # transmit closing string and recieve test results.
  server_conn = openconn(mycontext["server_ip"], mycontext["tcp_port"])
  server_conn.send("Done.")
  
  data = server_conn.recv(200)
  server_conn.close()
  print data

 
