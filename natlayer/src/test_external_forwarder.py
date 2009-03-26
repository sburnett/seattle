
include NATLayer_rpc.py

SERVER_ID = "THIS IS THE SERVER"
INTERVALS = .1
FORWARDER = "128.208.1.137"

def server_conn(remoteip, remoteport, socket, ch, superch):
  while True:
    data = socket.recv(128)
    if "END" in data:
      break
    else:
      sleep(INTERVALS)

def main():
  # Get a massive data file
  print getruntime(), "Open File Handle"
  fileh = open("junk_test.out")
    
  # Setup server waitforconn
  print getruntime(), "Doing a nat_waitforconn"
  handle = nat_waitforconn(SERVER_ID, 12345, server_conn,forwarderIP=FORWARDER,forwarderPort=12345)

  # Get a client socket
  print getruntime(), "Doing a nat_openconn"
  socket = nat_openconn(SERVER_ID,12345,forwarderIP=FORWARDER,forwarderPort=23456)  
  
  count = 0
  print getruntime(), "Sending data"
  while True:
    count += 1
    
    if (count % 20) == 0:
      print getruntime(), "Curr.",count
    
    try:
      data = fileh.read(1024)
      
      if data == "":
        break
    except Exception,e:
      print str(e)
      break
    
    try:  
      socket.send(data)
    except Exception, exp:
      print getruntime(), "Count:",count
      print getruntime(), "Exception:",str(exp)
      raise exp
    
  socket.send("END")
  
  print getruntime(), "Client done sending!"

if callfunc == "initialize":
  try:
    main()
  except Exception, exp:
    print getruntime(), "Last state",NAT_STATE_DATA["mux"].connectionInit, NAT_STATE_DATA["mux"].error
    print exp
    