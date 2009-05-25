
# Get the NATLayer
include NATLayer_rpc.py

if callfunc == "initialize":
  # Check our NAT status
  print getruntime()
  behind = behind_nat("128.208.1.140",23456)

  print getruntime(),behind
