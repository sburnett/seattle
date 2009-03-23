"""
<Program Name>
  PythonTCPBenchmark.py

<Started>
  February 15, 2009

<Author>                 
  Michael Moshofsky
  Richard Jordan
  Ivan Beschastnikh

<Purpose>
  Sends a specific amount of bytes with a specific chunk size and records the
  time that it required to complete.

  First argument tells program to be a server or client:
    Server: Only local port is needed in addition.
    Client: localPor, DestinationIP, DestinationPort, TotalBytes, and ChunkSize are needed.

  Arguments required: (-s or -c) LocalPort [DestinationIP DestinationPort TotalBytes ChunkSize]

<TODO>
  Right now the client cannot reuse its port, even if the socket is
  closed in clientSend(). Have to: (1) find out why this is the case
  and (2) set a socket reuse option so that the client can reuse the
  port.

  Need to extend the server to:
  - Be able to receive multiple connections and benchmark each one.

  Change the client-server benchmarking protocol to:
  - Have the client send the server the number of bytes it will send,
    so the server know how much data to expect.

  - Might want the server acknowledge the client's initial
    message. This might or might not be necessary since the server
    should do the benchmarking (see below).

  - Benchmark the time it takes the *server* to receive the data, not
    the time it takes the client to send the data, because send() is
    deceiving -- it queues data in kernel but does not indicate
    reception!
"""

import socket
import sys
import time


def serverListen(s):
  """
  <Purpose>
    Receive arbitrary amount of data from the client, and do
    absolutely nothing with it.
    
  <Arguments>
    s : socket object on which to listen and then receive
    
  <Exceptions>
    None
  
  <Side Effects>
    Acepts a connection and then receives data from the client on s
    
  <Returns>
    None
  """
  s.listen(1)
    
  conn, addr = s.accept()
  print 'Received connection from', addr

  while 1:
    try:
      data = conn.recv(1024)
    except:
      s.close()
      return



def clientSend(s, totalBytes, chunkSize):
  """
  <Purpose>
    Sends totalBytes worth of bytes in chunkSize chunks, and times how
    long it takes. Then closes the socket, prints out stats, and
    returns.
    
  <Arguments>
    s : socket on which to send (already connected)
    totalBytes : total bytes to send (int)
    chunkSize : number of chunks to send (e.g. this is some divisor of totalBytes) (int)
    
  <Exceptions>
    Socket exceptions
    
  <Side Effects>
    Sends data to a remote host.
    
  <Returns>
    None
  """
  totalChunks = totalBytes/chunkSize
  chunk = chunkSize * "a"

  startTime = time.clock()
  i = 0
  while (i < totalChunks):
    s.send(chunk)
    i += 1
  endTime = time.clock()

  runTime = (endTime - startTime) * 1.0

  addr = s.getpeername()
  s.close()

  print "\n\n******* Statistics for a Python TCP transfer *******"
  print "* Sent " + str(totalChunks) + " packets, which had a size of " + str(chunkSize) + " bytes." 
  print "* Total runtime: " + str(runTime) + " seconds."
  if runTime:
    print "* At a Rate of: " + str(totalBytes/runTime) + " B/S."
  print "*****************************************\n\n"
  return



def usage_exit(err_str = ""):
  """
  <Purpose>
    Prints an optional error message, and the usage for the program.
    
  <Arguments>
    err_str : the error to display to the user (string)
    
  <Exceptions>
    None
    
  <Side Effects>
    Prints to screen, and exits program.
    
  <Returns>
    None
  """
  if err_str != "":
    print "ERROR:", err_str
  print "usage: %s [-s|-c] LocalPort [DestinationIP DestinationPort TotalBytes ChunkSize]"%(sys.argv[0])
  sys.exit(1)



def main():
  """
  <Purpose>
    Parses arguments. Binds the socket that the client/server will use
    and runs the function to start either the client or the server. On
    argument parsing/valueerror calls usage_exit().
    
  <Arguments>
    None
    
  <Exceptions>
    None
    
  <Side Effects>
    None
    
  <Returns>
    None
  """
  # where are we?
  if len(sys.argv) < 3:
    usage_exit("at least three arguments are required")
    
  try:
    myport = int(sys.argv[2])
  except ValueError:
    usage_exit("LocalPort must be an integer")

  # who are we?
  serverOrClient = sys.argv[1]
  if serverOrClient not in ["-s", "-c"]:
    usage_exit("first argument must be -s or -c")

  # bind the socket that we will use
  myip = socket.gethostbyname(socket.getfqdn())
  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  s.bind((myip, myport))

  if serverOrClient == "-s":
    # we are the server
    serverListen(s)
    
  else:
    # we are the client
    if len(sys.argv) != 7:
      s.close()
      usage_exit("client (-c) needs exactly 5 other arguments")
      
    destip = sys.argv[3]
    try:
      destport = int(sys.argv[4])
    except ValueError:
      s.close()
      usage_exit("DestinationPort must be an integer")
      
    try:
      totalBytes = int(sys.argv[5])
    except ValueError:
      s.close()
      usage_exit("TotalBytes must be an integer")

    try:
      chunkSize = int(sys.argv[6])
    except ValueError:
      s.close()
      usage_exit("ChunkSize must be an integer")

    # now we can connect
    addr = (myip, destport)
    s.connect(addr)
    
    clientSend(s, totalBytes, chunkSize)
    
  return


# do it
if __name__ == "__main__":
  main()
