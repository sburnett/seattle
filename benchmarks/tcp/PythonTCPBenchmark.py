"""
<Program Name>
  PythonTCPBenchmark.py

<Started>
  February 15, 2009

<Author>                 
  Michael Moshofsky

<Purpose>
  Sends a specific amount of bytes with a specific chunk size and records the
  time that it required to complete.

  First argument tells program to be a server or client:
    Server: Only local port is needed in addition.
    Client: localPor, DestinationIP, DestinationPort, TotalBytes, and ChunkSize are needed.

  Arguments required: (-s or -c) LocalPort [DestinationIP DestinationPort TotalBytes ChunkSize]

"""
import socket
import sys
import time

def serverListen(s):
  s.listen(1)               
  conn, addr = s.accept()
  print 'Connected by', addr
  while 1:              
    data = conn.recv(1024)

  s.close()

import socket
import sys
import time


def serverListen(s):
  s.listen(1)
  conn, addr = s.accept()
  while 1:
    data = conn.recv(1024)
  conn.close()

def clientSend(s, totalBytes, chunkSize):
  totalChunks = totalBytes/chunkSize
  chunk = chunkSize * "a"

  startTime = time.clock()
  i = 0
  while (i < totalChunks):
    s.send(chunk)
    i += 1
  endTime = time.clock()

  runTime = endTime - startTime * 1.0

  addr = s.getpeername()
  s.close()

  print "\n\n******* Statistics for Python TCP *******"
  print "* Connected to " + str(addr)
  print "* Sent " + str(totalChunks) + " packets, which had a size of " + str(chunkSize) + " bytes." 
  print "* Total runtime: " + str(runTime) + " seconds."
  if runTime:
    print "* At a Rate of: " + str(totalBytes/runtime) + " B/S."
  print "*****************************************\n\n"


def main():
  # where are we?
  myport = int(sys.argv[2])
  myip = socket.gethostbyname(socket.gethostname())
  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  s.bind((myip, myport))

  # who are we?
  serverOrClient = sys.argv[1]
  if serverOrClient == "-s":
    serverListen(s)
  else: # client
    destip = sys.argv[3]
    destport = int(sys.argv[4])
    addr = (destip, destport)
    s.connect(addr)
    totalBytes = int(sys.argv[5])
    chunkSize = int(sys.argv[6])
    clientSend(s, totalBytes, chunkSize)

# do it
main()
