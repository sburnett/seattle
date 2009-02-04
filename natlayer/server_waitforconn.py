include NATLayer.py

# Must be pre-processed by repypp
# Takes 1 argument, the server's MAC

# Responds "Hi Back!" to every frame

def echoSocket(socket):
  while True:
    data = socket.recv(1024)
    if data != "":
      print data
      socket.send("Hi Back!")
    
def newClient(remotemac, socketlikeobj, thisnatcon):
  settimer(0, echoSocket, [socketlikeobj])

if callfunc == "initialize":
  mac = callargs[0]
  print "Connecting..."
  natcon = NATConnection(mac, "127.0.0.1", 12345)
  natcon.initServerConnection()
  print "Connected! Starting echo."
  
  natcon.waitforconn(newClient)
  
  print "Last Print"
