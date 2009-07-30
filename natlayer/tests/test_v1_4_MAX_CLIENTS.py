include NATLayer_rpc.repy

# This test connects a server to a forwarder and uses waitforconn
# Then it is tested to make the forwarder will reject clients once the max number
# is connected (currently 8 per server)


# There is no expected output

serverMac =  "SERVERSERVER"
MAX_CONNECTED = 4

# The test will be forced to exit after this many seconds
# This is necessary since client 3 is expected to block indefinately
TIME_LIMIT = 30

def new_client(remoteip, remoteport, socketlikeobj, commhandle, thisnatcon):
 
  #clients dont send so this should just block
  mesg = socketlikeobj.recv(1024)
  raise Exception, 'Unexpected message recieved by server: '+mesg
          
 



# This is called if the test is taking too long
def long_execution():
  print "Execution exceeded "+str(TIME_LIMIT)+" seconds!"
  exitall()
  



# run the test!
if callfunc == "initialize":

  #mycontext['forwarderip'] = '128.208.1.138'  # attu
  mycontext['forwarderip']= getmyip()       #local

  # a list of clients
  client_list = []
 
  # Setup timer to kill us if we exceed our time limit
  #handle = settimer(TIME_LIMIT, long_execution, ())
  
  # Create server connection, force local forwarder
  whandle = nat_waitforconn(serverMac, 10000, new_client, 
                  forwarderIP=mycontext['forwarderip'],
                  forwarderPort=12345,forwarderCltPort=12345) 
  
  number_connected = 0

  #set up clients
  for i in range(MAX_CONNECTED+1):
    clientmac = 'CLIENTNUM_'+str(i)
    if len(clientmac) <12: clientmac +='_'
    try:
      client_list.append(nat_openconn(serverMac, 10000,
             forwarderIP=mycontext['forwarderip'],forwarderPort=12345))
      number_connected +=1
    except Exception:
      if number_connected != MAX_CONNECTED: 
        print str(number_connected)+' of '+str(MAX_CONNECTED)+' clients connected'
        raise

 
  if number_connected != MAX_CONNECTED:
    print str(number_connected)+' of '+str(MAX_CONNECTED)+' clients connected'

  # exit the test
  exitall()
