"""
This file declares and sets the constant values used for the forwarder RPC interface

RPC requests are dictionaries that have special fields
A typical request would be like the following:

# Server requests to de-register
rpc_req = {"id":0,"request":"de_reg_serv"}

# Forwarder responds with success message
rpc_resp = {"id":0,"status":True,"value":None}

# To actually transfer this request, the following is necessary:
message = encode_rpc(rpc_req)
sock.send(message)

# Then, to receive a RPC mesg
rpc_mesg = decode_rpc(sock)

"""
# This is used to decode RPC dictionaries
include deserialize.py

# General Protocal Constants
RPC_VIRTUAL_IP = "0.0.0.0" # What IP is used for the virtual waitforconn / openconn
RPC_VIRTUAL_PORT = 0 # What virtual port to listen on for Remote Procedure Calls
RPC_FIXED_SIZE = 4   # Size of the RPC dictionary

# Defines fields
RPC_REQUEST_ID = "id"    # The identifier of the RPC request
RPC_FUNCTION = "request" # The remote function to call
RPC_PARAM = "value"      # The parameter to the requested function (if any)
RPC_ADDI_REQ = "additional" # Are there more RPC requests on the socket?
RPC_REQUEST_STATUS = "status" # The boolean status of the request
RPC_RESULT = "value"     # The result value if the RPC request

# Function Names
RPC_EXTERNAL_ADDR = "externaladdr"  # This allows the server to query its ip/port

# This allows a server to register with a forwarder
# This expects a MAC address as a parameter
RPC_REGISTER_SERVER = "reg_serv"    

# This allows a server to de-register from a forwarder
# This expects a MAC address as a parameter, or None to deregister all MAC's 
RPC_DEREGISTER_SERVER = "dereg_serv"

# The following two functions require an integer port and a server mac address
# # It expects the RPC_PARAM to be a dictionary:
# {"server":"__MAC__","port":50}
RPC_REGISTER_PORT = "reg_port"      # THis allows the server to register a wait port
RPC_DEREGISTER_PORT = "dereg_port"  # This allows the server to de-register a wait port

# This instructs the forwarder to begin forwarding data from this socket to a server
# It expects the RPC_PARAM to be a dictionary:
# {"server":"__MAC__","port":50}
RPC_CLIENT_INIT = "client_init"

# Helper Functions
def RPC_encode(rpc_dict):
  """
  <Purpose>
    Encodes an RPC request dictionary
  
  <Arguments>
    rpc_dict:
      A dictionary object
  
  <Returns>
    Returns a string that can be sent over a socket
  """
  rpc_dict_str = str(rpc_dict) # Conver to string
  rpc_length = str(len(rpc_dict_str)).rjust(RPC_FIXED_SIZE, "0") # Get length string
  return rpc_length + rpc_dict_str # Concatinate size with string

def RPC_decode(sock,blocking=False):
  """
  <Purpose>
    Returns an RPC request object from a socket
  
  <Arguments>
    sock:
      A socket that supports recv
    
    blocking:
      If the socket supports the blocking mode of operations, speicify this to be True
  
  <Returns>
    Returns a dictionary object containing the RPC Request
  """
  # Get the dictionary length
  # Then, Get the dictionary
  if blocking:
    length = int(sock.recv(RPC_FIXED_SIZE,blocking=True))
    dict_str = sock.recv(length,blocking=True)
  else:
    length = int(sock.recv(RPC_FIXED_SIZE))
    dict_str = sock.recv(length)
  
  dict_obj = deserialize(dict_str) # Convert to object
  return dict_obj
  