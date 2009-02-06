include NATLayer.py

# This test just attempts to create a NATConnection object, which should connect to the forwarder
# There is no expected output

if callfunc == "initialize":
  natcon = NATConnection("000000000000", "127.0.0.1", 12345)
  natcon.initServerConnection()
  natcon.close()