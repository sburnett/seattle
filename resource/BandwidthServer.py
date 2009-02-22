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
    self.idstring = ""
    self.creationtime = getruntime() # time that client initialized test
    self.packets = []
    self.intendedpackets = 0
    self.latestpackettime = -1.0
  
def get_info(client):  
  average_sum = 0
  number_averaged = 0
  totalbytes = 0
  packetcount = len(client.packets)
  for packet in client.packets:
    totalbytes += len(packet[0])
    
  for packet in client.packets:
    if packet[1] != -1:
      # If we have the time interval between it and the next, go ahead and
      # calculate bandwidth.
      cur_ave = len(packet[0]) / packet[1]
      average_sum += cur_ave
      number_averaged += 1
  
  if number_averaged < 1:
    print "Insufficient data to calculate bandwidth"
    return
    
  bytespersec = average_sum / number_averaged
  
  print
  print '===============', client.ip, '=================='
  print 'Packets:', packetcount , 'Expected:', client.intendedpackets
  print 'Packet size:', totalbytes / number_averaged, 'byte'
  print 'Total', totalbytes, 'Bytes  ', totalbytes / 1000, 'KB'
  print 'Bytes/sec:', bytespersec, '  KB/sec:', bytespersec / (1000)
  print '===================================================='
  return str(bytespersec)
  
# finalize will return the test data to the client and remove
# them from the global dictionary.  
def finalize(client_ip, conn):
  client = mycontext["clients"][client_ip]
  conn.send(get_info(client))
  conn.close()   
  del mycontext["clients"][client_ip]
  print "Client " + client_ip + " is finished."
  

def parse_packet(packet_str):
  packet_spl = packet_str.split("|")
  if len(packet_spl) < 2:
    raise Exception("Invalid packet")
  try:
    index = int(packet_spl[1])
  except ValueError:
    raise Exception("Invalid packet")

  return (packet_spl[0], int(packet_spl[1]))


# process_UDP handles all of the UDP connections, will ignore
# packets from clients who have not first initialized with a
# TCP connection. Valid clients will have packet stats updated
# in their Client instance.
def process_UDP(cl_ip, cl_port, mess, ch):
  
  # If the packet was not expected, it will be ignored.
  if cl_ip not in mycontext["clients"]:
    return
  
  client = mycontext["clients"][cl_ip]
  # The packet was expected, so check that it is valid and in the right
  # order.
  try:     
    idstring, newindex = parse_packet(mess)
  except Exception, err:
    if "Invalid packet" in str(err):
      print "Invalid packet from client " + cl_ip
      return
    raise err
  
  if len(client.packets) > 0:
    previouspacket = client.packets[-1]
    previndex = parse_packet(previouspacket[0])[1]
    
    if newindex > previndex + 1:
      # We missed a packet somewhere, so throw out the old one
      del client.packets[-1]
      client.packets.append([mess, -1])
      
    elif newindex < previndex + 1:
      # Packet is out of order, so don't add it
      pass
    
    else:
      # Valid ordering, so calculate and save the interval between the last packet
      # and this one
      interval = getruntime() - client.latestpackettime
      previouspacket = client.packets[-1]
      previouspacket[1] = interval
      client.packets[-1] = previouspacket
      # Then append this packet to our list
      client.packets.append([mess, -1])
  else:
    # We don't have any packets yet, so just go ahead and append this one
    client.packets.append([mess, -1])
    
  client.latestpackettime = getruntime()
    

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

