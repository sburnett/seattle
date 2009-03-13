
# Get the NATLayer
include NATLayer_rpc.py

if callfunc == "initialize":
  # Check our NAT status
  print getruntime()
  behind = behind_nat(forwarderIP="128.208.1.140",forwarderPort=23456)

  print getruntime(),behind