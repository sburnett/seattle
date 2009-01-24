include NATLayer.py

# Must be pre-processed by repypp
# Takes 2 arguments, IP to listen on and Port

# How much should we sample for the client sockets?
DATA_CHUNK = 1024

# How often should we sample the client sockets? (Time in seconds)
# Really, this is just how often new events are launched for each socket
SAMPLE_TIME = .1

events = {} # Tracks live events, servers
eventsClt = {} # For clients
client = {} # Tracks connected clients
server = {} # Tracks connected servers

# Checks all the sockets for data, and forwards everything
# TODO: make this (thread-)safe, e.g. iterating over dictionaries while running
def run():
  # Start an event for each server socket
  for srv in server:
    if not srv in events:
      #print "Sampling Server ", srv
      events[srv] = settimer(0,checkServerSocket,[srv])
  
  # Start an event for each client socket
  for clt in client:
    if not clt in eventsClt:
      #print "Sampling Client ", clt
      eventsClt[clt] = settimer(0,checkClientSocket,[clt])
      
# Checks a client socket for data
def checkClientSocket(clt):
  cltinfo = client[clt]
  data = cltinfo["socket"].recv(DATA_CHUNK)
  
  # Is there any data?
  if len(data) != 0:
    # Setup a frame, and send it to the server
    # TODO: make this thread-safe
    frame = NATFrame()
    frame.initAsDataFrame(clt,data)
    server[cltinfo["server"]].send(frame.toString())

  # Clean-up
  # TODO: make this thread safe
  if clt in eventsClt:
    del eventsClt[clt]
    
# Checks a server socket for data
# TODO: handle other server requests, like CONN_TERM and CONN_BUF_SIZE
def checkServerSocket(srv):
  # Get data from the server socket as a frame
  sock = server[srv]
  frame = NATFrame()
  frame.initFromSocket(sock)
  
  # Handle the case where the server is forwarded non-null data
  if frame.frameMesgType == DATA_FORWARD and frame.frameContentLength != 0:
    clt = frame.frameMACAddress
    clientSock = client[clt]["socket"]
    clientSock.send(frame.frameContent)

  # Clean-up
  # TODO: make this thread safe
  if srv in events:
    del events[srv]


# Handles a new connection to the forwarder
# Should this launch an event? Maybe.
def handleit(socket, frame):
  # Setup server, and acknowledge it
  if frame.frameMesgType == INIT_SERVER:
    server[frame.frameMACAddress] = socket
    resp = NATFrame()
    resp.initAsForwarderResponse(STATUS_CONFIRMED)
    socket.send(resp.toString())
  
  # Setup client, and acknowledge
  # TODO: keep track of number of client -> server connections  and implement
  # STATUS_BSY_SERVER
  if frame.frameMesgType == INIT_CLIENT:
    serverMac = frame.frameContent
    if serverMac in server:
      client[frame.frameMACAddress] = {"socket":socket,"server":frame.frameContent}
      resp = NATFrame()
      resp.initAsForwarderResponse(STATUS_CONFIRMED)
      socket.send(resp.toString())
    else: # Server is not available on forwarder, error.
      resp = NATFrame()
      resp.initAsForwarderResponse(STATUS_NO_SERVER)
      socket.send(resp.toString())
      socket.close()

# Does everything    
if callfunc == "initialize":
  # Initialize the NAT channel
  natcon = NATConnection(FORWARDER_MAC, callargs[0], int(callargs[1]))
  
  # Setup our process to handle everything
  natcon.frameHandler = handleit
  
  # Check all the sockets once in a while
  # TODO: Use threads?
  while True:
    run()  
    sleep(SAMPLE_TIME)
