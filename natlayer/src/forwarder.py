include NATLayer.py

# Must be pre-processed by repypp
# Takes 2 arguments, IP to listen on and Port

# How much should we sample for the client sockets?
DATA_CHUNK = 1024

# How often should we sample the client sockets? (Time in seconds)
# Really, this is just how often new events are launched for each socket
SAMPLE_TIME = .25

events = {} # Tracks live events, servers
eventsClt = {} # For clients
client = {} # Tracks connected clients
server = {} # Tracks connected servers

RESTART_INTERVAL = 1 # How many seconds between checking main loop status

# Checks all the sockets for data, and forwards everything
# Im considering making this method into two seperate threads
# one for checking server sockets, and another for the client
# sockets.  
def run():
  try:
    # We are running now...
    mycontext['MAIN_LOOP_RUNNING'] = True
    while True:
    
      # Start an event for each server socket
      mycontext['srv-lock'].acquire()
      for srv in server:
        if not srv in events:
          #print "Sampling Server ", srv
          events[srv] = settimer(0,checkServerSocket,[srv,server[srv]])
      mycontext['srv-lock'].release()

      # Start an event for each client socket
      mycontext['cl-lock'].acquire()
      for clt in client:
        if not clt in eventsClt:
          #print "Sampling Client ", clt
          eventsClt[clt] = settimer(0,checkClientSocket,[clt,client[clt]])
      mycontext['cl-lock'].release()
    
      sleep(SAMPLE_TIME)
  except:
    # Set the flag, so we restart
    print "Exception in Main Loop!"

  finally:
    # Set the flag that we are stopped, so the main thread restarts us
    mycontext['MAIN_LOOP_RUNNING'] = False

# Checks a client socket for data
  # Armon, i changed the arguments so this method does not have to read
  # the client data structure and -> does not wait for a lock to start
def checkClientSocket(clt,cltinfo):
  #cltinfo = client[clt]
  
  # Run as long as possible, and clean-up on error
  try:
    while True:
          
      data = cltinfo["socket"].recv(DATA_CHUNK)
  
      # Is there any data?
      if len(data) != 0:
        # Setup a frame, and send it to the server
        # TODO: make this thread-safe
        frame = NATFrame()
        frame.initAsDataFrame(clt,data)
        server[cltinfo["server"]].send(frame.toString())
      else:
        # Connection is closed, shutdown socket and thread
        raise Exception, "Client Disconnected!"

  except Exception, exp:
    # Exit cleanly, close the socket
    # TODO: send CONN_TERM to connected server
    print "Exception Checking Client Socket! ", type(exp), exp
    mycontext['cl-lock'].acquire()
    try:
      client[clt]["socket"].close()
    except:
      pass
    del client[clt]
    mycontext['cl-lock'].release()
      
  finally:
    # Clean-up
    mycontext['cl-lock'].acquire()
    if clt in eventsClt:
      del eventsClt[clt]
    mycontext['cl-lock'].release()
    

# Checks a server socket for data
# TODO: handle other server requests, like CONN_TERM and CONN_BUF_SIZE
  # Armon, i changed the arguments so this method does not have to read
  # the server data structure and -> does not wait for a lock to start
def checkServerSocket(srv,sock):
  # Run as long as possible, and clean-up on error
  try:
    while True:
      # Get data from the server socket as a frame
      frame = NATFrame()
      frame.initFromSocket(sock)
  
      # Handle the case where the server is forwarded non-null data
      if frame.frameMesgType == DATA_FORWARD and frame.frameContentLength != 0:
        try:
          clt = frame.frameMACAddress
          clientSock = client[clt]["socket"]
          clientSock.send(frame.frameContent)
        except KeyError:
          # The client is no longer connected...
          # TODO send server CONN_CLOSE
          pass

  except Exception, exp:
    # Exit cleanly, and close the socket
    # TODO: close the connection to all clients connected to this server
    print "Exception Checking Server Socket! ", type(exp), exp
    mycontext['srv-lock'].acquire()
    try:
      server[srv]["socket"].close()
    except:
      pass
    del server[srv]
    mycontext['srv-lock'].release()
  
  finally:
    # Clean-up
    mycontext['srv-lock'].acquire()
    if srv in events:
      del events[srv]
    mycontext['srv-lock'].release()


# Handles a new connection to the forwarder
# Should this launch an event? Maybe.
def handleit(socket, frame):
  # Setup server, and acknowledge it
  if frame.frameMesgType == INIT_SERVER:
    mycontext['srv-lock'].acquire()
    server[frame.frameMACAddress] = socket
    resp = NATFrame()
    resp.initAsForwarderResponse(STATUS_CONFIRMED)
    socket.send(resp.toString())
    mycontext['srv-lock'].release()

  # Setup client, and acknowledge
  # TODO: keep track of number of client -> server connections  and implement
  # STATUS_BSY_SERVER
  if frame.frameMesgType == INIT_CLIENT:
    serverMac = frame.frameContent
    mycontext['srv-lock'].acquire()
    found_server = (serverMac in server)
    mycontext['srv-lock'].release()
    if found_server:
      mycontext['cl-lock'].acquire()
      client[frame.frameMACAddress] = {"socket":socket,"server":frame.frameContent}
      resp = NATFrame()
      resp.initAsForwarderResponse(STATUS_CONFIRMED)
      socket.send(resp.toString())
      mycontext['cl-lock'].release()

    else: # Server is not available on forwarder, error.
      resp = NATFrame()
      resp.initAsForwarderResponse(STATUS_NO_SERVER)
      socket.send(resp.toString())
      socket.close()


# Does everything    
if callfunc == "initialize":
 
  #setup locks for client and server data structures  
  mycontext['srv-lock'] =getlock()
  mycontext['cl-lock'] =getlock()
  
  # Initialize the NAT channel
  natcon = NATConnection(FORWARDER_MAC, callargs[0], int(callargs[1]))
  #natcon = NATConnection(FORWARDER_MAC,"127.0.0.1" , 12345)

  # Setup our process to handle everything
  natcon.frameHandler = handleit
  
  # Its not running yet...
  mycontext['MAIN_LOOP_RUNNING'] = False
  
  while True:
    # Start / Restart the main loop
    if not mycontext['MAIN_LOOP_RUNNING']:
      print "Starting Main Loop..."
      # Check all the sockets once in a while
      settimer(0,run,[])
    sleep(RESTART_INTERVAL)
