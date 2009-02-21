"""
<Program Name> 
  BandwidthServer.py

<Started>
  Feb 2 2009

<Authors> 
  Anthony Honsta 
  Carter Butaud

<Purpose>
  To receive packet trains from clients and calculate the 
  bandwidth between the server and client so that 10% can
  properly approximated.
  
<Questions> Anthony - is it possible for the poll_clients and finalize
  to both race to delete the key from the dictionary resulting in a 
  key error? Should we check or is this a race condition that could 
  be solved with a lock?
  
<Description>
  Operations are as follows.
  1) a) Client connects with TCP connection
     b) Server receives and handles connection with process_TCP function
          If client is not already in the global dictionary, a new
          Client object is created and added. 
     c) Client transmits # of packets to be sent.
     d) Server closes TCP connection.
        
  2) a) Client begins sending UDP packets
     b) Server handles them with process_UDP and 
        updates the Client object.
     
  3) a) Client connects with TCP connection
     b) Server receives and handles connection with process_TCP function
     c) Client transmits closing signal
     d) Server passes the socket and client ip to the finalize 
        function. 
        finalize - the bandwidth results are transmited back
        to the client (bytes/sec). finalize removes the
        client from the dictionary and closes TCP socket.
        
   Server clean up -
     If the client does not properly initiate the 2nd and final
     tcp connection, no results will be transmited and after a 
     set time (10seconds) the server will remove them from the dictionary.
"""
class Client():
  def __init__(self):
    self.ip = '0.0.0.0'
    self.creationtime = getruntime() # time that client initialized test
    self.packetcount = 0
    self.intendedpackets = 0
    self.totalbytes = 0
    self.startrectime = getruntime() # time that first packet was received
    self.latestpacket = getruntime()
  
def get_info(client):
    
  #Need to ensure get_info does no execute if packet count is 0 or 1.
  if(client.packetcount < 2):
    print "Insufficent data recieved"
    #SHOULD RETURN DEFAULT
    
  bytesec = (client.totalbytes) / (client.latestpacket - client.startrectime)
  
  print
  print '===============', client.ip, '=================='
  print 'Packets:', client.packetcount , 'Expected:', client.intendedpackets
  print 'Packet size:', client.totalbytes / client.packetcount, 'byte'
  print 'Total', client.totalbytes, 'Bytes  ', client.totalbytes / 1000, 'KB'
  print 'Bytes/sec:', bytesec, '  KB/sec:', bytesec / (1000)
  print '===================================================='
  return str(bytesec)
  
# finalize will return the test data to the client and remove
# them from the global dictionary.  
def finalize(client_ip, conn):
  client = mycontext["clients"][client_ip]
  conn.send(get_info(client))
  conn.close()   
  del mycontext["clients"][client_ip]
  print "Client " + client_ip + " is finished."

# process_UDP handles all of the UDP connections, will ignore
# packets from clients who have not first initialized with a
# TCP connection. Valid clients will have packet stats updated
# in their Client instance.
def process_UDP(cl_ip, cl_port, mess, ch):
  
  # If the packet was not expected, it will be ignored.
  if cl_ip not in mycontext["clients"]:
    return
  
  client = mycontext["clients"][cl_ip]
  # The packet was expected there for we update the Client
  # object with new data.     
  client.packetcount += 1
  client.totalbytes += len(mess)
  client.latestpacket = getruntime()
    

def process_TCP(client_ip, client_port, conn, th, lh):
    
  # If the client is known, test to see if client has
  # notified the server its "Done." 
  if client_ip in mycontext["clients"]:
    client = mycontext["clients"][client_ip]
    result = conn.recv(50)
    # Client notifies server that it is finished
    # Anthony - should we close the just because there
    # was a second connection, or should we check for this
    # "Done." string?
    if(result == "Done."):
      finalize(client_ip, conn)
      return
    else: # for DEBUG 
      # Have mostly seen initlial tcp connections with no data
      # but it could occur here, should it finalize or close?
      print "***DEBUG: result is -", result # for DEBUG
    conn.close()
    return
   
  # This is the clients initial connection with the server.
  # Add it to the dictionary and initiate instance of Client.
  new_client = Client()
  new_client.ip = client_ip
  new_client.creationtime = getruntime()
  data = conn.recv(50)
  try:
    data = int(data)
  except ValueError:
    print "***Error, tcp probe opened with: ", str(data)
  new_client.intendedpackets = data
  mycontext["clients"][client_ip] = new_client   
  
  print "New client " + client_ip + " intends to send " + str(data) + " packets."
  
# Will remove clients who have been in the dictionary for more
# then 10 seconds.
def poll_clients(time_to_wait):
  print "Polling clients"
  
  # To prevent an error resulting in the 
  # dictionary changing while we iterate, create
  # a copy to store all the keys we plan to delete.
  to_close = []
  for client_ip in mycontext["clients"].keys():
    client = mycontext["clients"][client_ip]
    clientage = (getruntime() - client.creationtime)
    if(clientage > 10.0):
      to_close.append(client)
  for oldclient in to_close:
    del mycontext["clients"][oldclient.ip]
    print "Client " + oldclient.ip + " was dropped."
  
  # restart the clean up timer.  
  settimer(time_to_wait, poll_clients, [time_to_wait])


if callfunc == "initialize":
  ip = getmyip()
  mycontext["tcp_port"] = 12345
  mycontext["udp_port"] = 12346
  mycontext["clients"] = {}
  print "Listening on " + ip + ":" + str(12345)
  waitforconn(ip, mycontext["tcp_port"], process_TCP)
  recvmess(ip, mycontext["udp_port"], process_UDP)
  settimer(15, poll_clients, [15])

