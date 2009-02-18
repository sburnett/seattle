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
  
  Arguments required: LocalPort DestinationIP DestinationPort TotalBytes ChunkSize

"""
import time



myport = argv[0]
destip = argv[1]
destport = int(argv[2])
totalBytes = int(argv[3])
chunkSize = int(argv[4])
totalChunks = totalBytes/chunkSize
chunk = ""
i = 0

while (i < totalChunks):
  chunk += "a"
  i += 1

i = 0
socket = socket()
socket.bind(getmyip(), myport)
socket.connect(destip, destport)
startTime = time.clock()

while (i < totalChunks):
  socket.send(chunk)
  i += 1

endTime = time.clock()

print "Total runtime: " + (endTime - startTime) + " seconds.\n"
print "Rate: " + ((endTime - startTime)/ totalBytes) + " bytes/second.\n"

