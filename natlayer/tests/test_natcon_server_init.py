include NATLayer.py

# This test just attempts to create a NATConnection object, which should connect to the forwarder

if callfunc == "initialize":
  natcon = NATConnection("111111111111", "127.0.0.1", 12345)
  natcon.initServerConnection()
  natcon.close()