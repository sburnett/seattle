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

  avgDiff = 0
  packets = 0
  
  # Print message everyX packets
  everyX = 20
  
  num = 1
  while True:
    run = getruntime()
    socket.send(str(num))
    num = num + 1
    data = socket.recv(1024)
    if data == str(num):
      num = num + 1
      diff = getruntime()-run
      avgDiff = (avgDiff + diff)
      packets = packets +1
      
      if packets % everyX == 0:
        print packets, ": Got Response! ", (1/diff), "Packets/sec ",  (1/(avgDiff/packets)), " Avg. Packets/sec"
