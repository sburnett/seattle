# This test tries to use mux_waitforconn and mux_openconn.
# It then attempts to exchange the numbers 1 to 100

# Get the Multiplexer
include Multiplexer.py

INTERVAL = 49

# Handle a new virtual connection
def new_virtual_conn(remoteip, remoteport, virtualsock, junk, multiplexer):
  num = 0
  part = ""
  while True:
    data = virtualsock.recv(1024)
    if data == str(num):
      num = num + 1
      virtualsock.send(str(num))
      num = num + 1
    else:
      print "Serv. Unexpected number! Expected: ", str(num), " Received: ",data
      part += data
      
      if part == str(num):
        part = ""
        num = num + 1
        virtualsock.send(str(num))
        num = num + 1


# Setup a waitforconn on a real socket
mux_waitforconn("127.0.0.1", 12345, new_virtual_conn)

# Try to connect to the other multiplexer
virtualsock = mux_openconn("127.0.0.1", 12345)

start = getruntime()
maxrate = 0
try:
  data = "-1"
  num = -1
  part = ""
  while True:
    try:
      if (num % INTERVAL) == 0:
        time = getruntime()-start
        avg = (num/time)
        INTERVAL = (int(avg)/2)*4-1
        maxrate = max(maxrate, avg)
        print round(time,2), "Average", round(avg,2), "mesg./sec.","("+str(num)+")"
    except ZeroDivisionError:
      INTERVAL = 50
      
    if data == str(num):
      num = num + 1
      virtualsock.send(str(num))
      num = num + 1
    else:
      print "Client Unexpected number! Expected: ", str(num), " Received: ",data
      part += data
      
      if part == str(num):
        part = ""
        num = num + 1
        virtualsock.send(str(num))
        num = num + 1
        
    data = virtualsock.recv(1024)

except KeyboardInterrupt:
  print "Runtime: ",getruntime()-start
  print "Fastest: ",maxrate," mesg./sec."


exitall()