# This test tries to test for proper connection buffering
# It does this by hooking into the multiplexers internal functions and by counting the number
# of CONN_BUF_SIZE messages sent. The buffer is also decreased substantially to speed this up.

# Get the Multiplexer
include Multiplexer.py

MAX_NUM = 50
BUF_SIZE = 1

# Hook into the mux's handling of CONN_BUF_SIZE frames, count the number of calls
def server_conn_buf_size(socket, num):
  # Increment the counter, then call the real function
  mycontext["servernum"] += 1
  realfunc = mycontext["serverfunc"]
  realfunc(socket, num)

def client_conn_buf_size(socket, num):
  # Increment the counter, then call the real function
  mycontext["clientnum"] += 1
  realfunc = mycontext["clientfunc"]
  realfunc(socket, num)  

# Handle a new virtual connection
def new_virtual_conn(remoteip, remoteport, virtualsock, junk, multiplexer):
  # Change the default buffer size
  multiplexer.defaultBufSize = BUF_SIZE
  
  # Intercept the servers function
  mycontext["serverfunc"] = multiplexer._conn_buf_size
  multiplexer._conn_buf_size = server_conn_buf_size
  
  # Change the socket buffers
  virtualsock.bufferInfo = {"incoming":BUF_SIZE,"outgoing":BUF_SIZE}
  
  # Exchange 1 to 100
  num = 0
  part = ""
  while True and num < MAX_NUM:
    data = virtualsock.recv(1024)
    if data == str(num):
      num = num + 1
      mycontext["length"] += len(str(num))
      virtualsock.send(str(num))
      num = num + 1
    else:
      # print "Srv. Unexpected number! Expected: ", str(num), " Received: ",data
      part += data
      if part == str(num):
        part = ""
        num = num + 1
        mycontext["length"] += len(str(num))
        virtualsock.send(str(num))
        num = num + 1

def timeout():
  print "Reached timeout!"
  exitall()

if callfunc=='initialize':
  # Kill us in 20 seconds
  settimer(20, timeout,())

  # Setup counters for the server and client conn_buf messages
  mycontext["clientnum"] = 0
  mycontext["servernum"] = 0
  
  # Setup pointers to the original functions
  mycontext["clientfunc"] = None
  mycontext["serverfunc"] = None
  
  # Length of data sent
  mycontext["length"] = 0
  
  # Setup a waitforconn on a real socket
  mux_waitforconn("127.0.0.1", 12345, new_virtual_conn)

  # Try to connect to the other multiplexer
  virtualsock = mux_openconn("127.0.0.1", 12345)

  # Change the default buffer size
  mux = MULTIPLEXER_OBJECTS["IP:127.0.0.1:12345"]
  mux.defaultBufSize = BUF_SIZE
  
  # Intercept the clients function
  mycontext["clientfunc"] = mux._conn_buf_size
  mux._conn_buf_size = client_conn_buf_size
  
  # Change the socket buffers
  virtualsock.bufferInfo = {"incoming":BUF_SIZE,"outgoing":BUF_SIZE}
  
  # Try to exchange 1 to 10
  num = -1
  data = "-1"
  part = ""
  
  while True and num < MAX_NUM:
    if data == str(num):
      num = num + 1
      if num == MAX_NUM:
        break
      mycontext["length"] += len(str(num))
      virtualsock.send(str(num))
      num = num + 1
      
    else:
      # print "Clt. Unexpected number! Expected: ", str(num), " Received: ",data
      part += data
      if part == str(num):
        part = ""
        num = num + 1
        if num == MAX_NUM:
          break
        mycontext["length"] += len(str(num))
        virtualsock.send(str(num))
        num = num + 1
    
    data = virtualsock.recv(1024)
  
  # Let everything settle
  sleep(2)
  
  # We expect to see MAX_NUM-1 calls to _conn_buf_size, evenly divided between client and server
  if mycontext["clientnum"] != mycontext["servernum"]:
    print "Uneven number of calls to buffer functions. Client:",mycontext["clientnum"],"Server:",mycontext["servernum"]
  
  # Expected is the length of all messages sent, divided by the default buffer size
  expected = (mycontext["length"] / BUF_SIZE)
  actual = mycontext["clientnum"] + mycontext["servernum"]
  if actual != expected:
    print "Unexpected number of buffer calls! Expected:",expected,"Actual:",actual

  exitall()