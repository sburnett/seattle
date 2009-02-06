include NATLayer.py

# This test just attempts to create a NATConnection object, which should connect to the forwarder
# as the server. Then it creates a second NATConnection object which should be a client (to the same server)
# There is no expected output

if callfunc == "initialize":
  serverMac = "123456123456"
  clientMac = "654321654321"
  
  natcon = NATConnection(serverMac, "127.0.0.1", 12345)
  natcon.initServerConnection()

  natcon2 = NATConnection(clientMac, "127.0.0.1", 12345)
  natcon2.initClientConnection(serverMac)
  
  natcon2.close()
  natcon.close()