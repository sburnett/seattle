resource cpu .90
resource memory 150000000   # 150 Million bytes
resource diskused 400000000 # 800 MB
resource events 1000
resource filewrite 1000000
resource fileread 1000000
resource filesopened 500
resource insockets 500
resource outsockets 500
resource netsend 10000000
resource netrecv 10000000
resource loopsend 100000000
resource looprecv 100000000
resource lograte 3000000
resource random 10000
resource messport 50011 #used for testing purposes only
resource connport 50010 #registration server expects incoming tcp registration requests on this port
resource messport 50010 #registration server expects incoming UDP requests on this port
resource connport 50014 #update server expects incoming tcp registration requests on this port
resource messport 50014 #update server expects incoming UDP requests on this port
resource connport 50016 #used by query server
resource messport 50016 #used by query server
resource connport 50012 #this port is used for testing client communication, NOT USED BY SERVER
resource messport 50012 #this port is used for testing client communication, NOT USED BY SERVER
resource connport 50013 #this port is used for testing client communication, NOT USED BY SERVER
resource messport 50013 #this port is used for testing client communication, NOT USED BY SERVER
resource messport 34612   # use for getting an NTP update


call gethostbyname_ex allow
call sendmess allow
call stopcomm allow 			# it doesn't make sense to restrict
call recvmess allow
call openconn allow
call waitforconn allow
call socket.close allow 		# let's not restrict
call socket.send allow 			# let's not restrict
call socket.recv allow 			# let's not restrict
call open allow 			# can read / write all
call file.__init__ allow 		# can read / write all
call file.close allow 			# shouldn't restrict
call file.flush allow 			# they are free to use
call file.next allow 			# free to use as well...
call file.read allow 			# allow read
call file.readline allow 		# shouldn't restrict
call file.readlines allow 		# shouldn't restrict
call file.seek allow 			# seek doesn't restrict
call file.write allow 			# shouldn't restrict (open restricts)
call file.writelines allow 		# shouldn't restrict (open restricts)
call sleep allow			# harmless
call settimer allow			# we can't really do anything smart
call canceltimer allow			# should be okay
call exitall allow			# should be harmless 

call log.write allow
call log.writelines allow
call getmyip allow			# They can get the external IP address
call listdir allow			# They can list the files they created
call removefile allow			# They can remove the files they create
call randomfloat allow			# can get random numbers
call getruntime allow			# can get the elapsed time
call getlock allow			# can get a mutex
