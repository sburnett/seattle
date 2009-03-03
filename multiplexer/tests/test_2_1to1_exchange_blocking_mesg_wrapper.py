# This test tries to use mux_waitforconn and mux_openconn.
# It attempts to exchange messages, where the send is half the recv,
# to test that blocking is working

# Get the Multiplexer
include Multiplexer.py

# How many times to transmit?
MAX_NUM = 10

# Message
MESG = "0123456789"
RECV_SIZE = 10
SEND_SIZE = 5
SEND_PART = 2

# Handle a new virtual connection
def new_virtual_conn(remoteip, remoteport, virtualsock, junk, multiplexer):
  for x in xrange(MAX_NUM):
    mesg = virtualsock.recv(RECV_SIZE, True)
    if mesg != MESG:
      print "Got wrong message! Expect:",MESG,"Got:",mesg
      exitall()
  
  # Finish
  exitall()

def timeout():
  print "Reached timeout!"
  exitall()

if callfunc=='initialize':
  # Kill us in 15 seconds
  settimer(15, timeout,())

  # Setup a waitforconn on a real socket
  mux_waitforconn("127.0.0.1", 12345, new_virtual_conn)

  # Try to connect to the other multiplexer
  virtualsock = mux_openconn("127.0.0.1", 12345)

  # Try to exchange, sending only part of the whole message
  for x in range(MAX_NUM*2):
    x = x % SEND_PART
    send = MESG[x*SEND_SIZE:(x+1)*SEND_SIZE]
    virtualsock.send(send)
    sleep(.25)
  
  sleep(1)
