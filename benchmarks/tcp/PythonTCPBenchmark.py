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

TOTAL_BYTES = 10000000       
CHUNK_SIZE = 100000   
TOTAL_CHUNKS = (TOTAL_BYTES/CHUNK_SIZE) * 1.0 # 100 packets
CHUNK = CHUNK_SIZE * "a" # all the letter 'a'

IP = socket.gethostbyname(socket.getfqdn())
PEER='attu.cs.washington.edu'
S_PORT = 12345
C_PORT = 12346


def serverListen():
  server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  server.bind((IP, S_PORT))
  server.listen(1)
  conn, addr = server.accept()

  startTime = time.clock()
  bytes_rcvd = 0
  while bytes_rcvd < TOTAL_BYTES:
    data = conn.recv(TOTAL_BYTES)
    bytes_rcvd += len(data)
  endTime = time.clock()

  runTime = (endTime - startTime) * 1.0

  print "\n\n******* Statistics for Python TCP *******"
  print "Sent " + str(TOTAL_CHUNKS) + " packets, which had a size of " + str(CHUNK_SIZE) + " bytes." 
  print "Total runtime: " + str(runTime) + " seconds."
  if runTime:
    print "At a Rate of: " + str(TOTAL_BYTES * 1.0/runTime) + " B/S."

def clientSend():
  conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#  conn.bind((IP, C_PORT))
  conn.connect((IP, S_PORT))
  
  packetNum = 0
  while (packetNum < TOTAL_CHUNKS):
    conn.send(CHUNK)
    packetNum += 1
  
  conn.close()

def usage():
  print "Usage: python PythonTCPBenchmark.py (-s or -c)"

def main():
  serverOrClient = sys.argv.pop()
  if serverOrClient == "-s":
    serverListen()
  elif serverOrClient == "-c":
    clientSend()
  else:
    usage()

# do it
if __name__ == "__main__":
  main()

