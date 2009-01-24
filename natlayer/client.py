include NATLayer.py

# Must be pre-processed by repypp
# Takes 2 arguments, first is the local MAC, second is the server MAC

# Connects to forwarder, sends "Hi There!" to a server, and waits for "Hi Back!"

if callfunc == "initialize":
  mac = callargs[0]
  mac2 = callargs[1]
  print "Connecting..."
  natcon = NATConnection(mac, "127.0.0.1", 12345)
  socket = natcon.initClientConnection(mac2)

  if socket == None:
    print "Error!", natcon.error
    exit()

  print "Connected! Saying hi now."

  while True:
    socket.send("Hi There!")
    sleep(.5)
    data = socket.recv(1024)
    if data == "Hi Back!":
      print "Got Response!"
