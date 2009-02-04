include NATLayer.py

# Must be pre-processed by repypp
# Takes 1 argument, the server's MAC

# Responds "Hi Back!" to every frame

if callfunc == "initialize":
  mac = callargs[0]
  print "Connecting..."
  natcon = NATConnection(mac, "127.0.0.1", 12345)
  natcon.initServerConnection()
  print "Connected! Starting echo."
  
  while True:
    frame = natcon.recv()
    num = int(frame.frameContent)
    
    natcon.send(frame.frameMACAddress, str(num+1))
    
