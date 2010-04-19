###INFORMATION###
#This is a modified version of all pairs ping designed to test the cnc system
#Unlike allpairsping.py, this code reads from a file that gives an available port on each neighbor as well as the ip

#Usage: cncallpairsping.py [no arguments]
#the file NEIGHBOR_INFO_FILE_NAME must list each neighbor on a separate line, where each neighbor is represented as a space separated ip port pair.

NEIGHBOR_INFO_FILE_NAME = "neighboripportlist.txt"

# send a probe message to each neighbor
def probe_neighbors():

  for neighbor in mycontext["neighborlist"]:
    neighborip, neighborport = neighbor
    mycontext['sendtime'][neighbor] = getruntime()
    sendmess(neighborip, neighborport, 'ping',getmyip(), mycontext['myport'])
    
    localvessel = getmyip(), mycontext['myport']
    sendmess(neighborip, neighborport,'share'+encode_row(localvessel, mycontext["neighborlist"], mycontext['latency'].copy()),getmyip(), mycontext['myport'])
    # sleep in between messages to prevent us from getting a huge number of 
    # responses all at once...
    sleep(.5)

  # Call me again in 10 seconds
  while True:
    try:
      settimer(10,probe_neighbors,[])
      return
    except Exception, e:
      if "Resource 'events'" in str(e):
        # there are too many events scheduled, I should wait and try again
        sleep(.5)
        continue
      raise
  


# Handle an incoming message
def got_message(srcip,srcport,mess,ch):
  src_ipport_pair = srcip, srcport
  if mess == 'ping':
    sendmess(srcip,srcport,'pong', getmyip(), mycontext['myport'])
  elif mess == 'pong':
    # elapsed time is now - time when I sent the ping
    mycontext['latency'][src_ipport_pair] = getruntime() - mycontext['sendtime'][src_ipport_pair]

  elif mess.startswith('share'):
    mycontext['row'][src_ipport_pair] = mess[len('share'):]



def encode_row(row_ipport_pair, neighborlist, latencylist):

  retstring = "<tr><td>"+row_ipport_pair[0] + ":" + str(row_ipport_pair[1]) +"</td>"
  for neighbor in neighborlist:
    neighborip, neighborport= neighbor
    if neighbor in latencylist:
      retstring = retstring + "<td>"+str(latencylist[neighbor])[:4]+"</td>"
    else:
      retstring = retstring + "<td>Unknown</td>"

  retstring = retstring + "</tr>"
  return retstring


# Displays a web page with the latency information
def show_status(srcip,srcport,connobj, ch, mainch): 

  webpage = "<html><head><title>Latency Information</title></head><body><h1>Latency information from "+getmyip()+' </h1><table border="1">'
  
  #get a string representation of each neighbor
  neighborstringlist=[]
  for neighborip, neighborport in mycontext['neighborlist']:
    neighborstringlist.append(neighborip+":"+str(neighborport))  
  
  webpage = webpage + "<tr><td></td><td>"+ "</td><td>".join(neighborstringlist)+"</td></tr>"

  # copy to prevent a race
#  connobj.send(encode_row(getmyip(), mycontext['neighborlist'], mycontext['latency'].copy()))

  for nodeip, nodeport in mycontext['neighborlist']:
    node_ipport_pair = nodeip, nodeport
    if node_ipport_pair in mycontext['row']:
      webpage = webpage + mycontext['row'][node_ipport_pair]+'\n'
    else:
      webpage = webpage + '<tr><td>'+nodeip + ":" + str(nodeport) +'</td><td>No Data Reported</td></tr>\n'

  # now the footer...
  webpage = webpage + '</table></html>'

  # send the header and page
  connobj.send('HTTP/1.0 200 OK\nContent-Length: '+str(len(webpage))+'\nDate: Fri, 31 Dec 1999 23:59:59 GMT\nContent-Type: text/html\n\n'+webpage) 

  # and we're done, so let's close this connection...
  connobj.close()



if callfunc == 'initialize':

  # this holds the response information (i.e. when nodes responded)
  mycontext['latency'] = {}

  # this remembers when we sent a probe
  mycontext['sendtime'] = {}

  # this remembers row data from the other nodes
  mycontext['row'] = {}
  
  # get the nodes to probe
  #used to store neighbor ip,port pairs
  mycontext['neighborlist'] = []
  
  f = open(NEIGHBOR_INFO_FILE_NAME, mode='r')
  for line in f:
    raw_data = line.strip()
    ip, port_str = raw_data.split()
    port = int(port_str)
    vessel_entry = ip, port
    mycontext['neighborlist'].append(vessel_entry)
  f.close()

  ip = getmyip() 
  #if len(callargs) != 1:
  #  raise Exception, "Must specify the port to use for cnc communcation"
  #mycontext['cncport']= int(callargs[0])
  
  #we need to use the port assigned to this address in the NEIGHBOR_INFO_FILE_NAME file'
  pingport = None
  for ip_search, port_search in mycontext['neighborlist']:
    if ip_search==ip:
      pingport = port_search
      break
  
  mycontext['myport']=pingport
  
  # call gotmessage whenever receiving a message
  recvmess(ip,pingport,got_message)  

  probe_neighbors()

  # we want to register a function to show a status webpage (TCP port)
  pageport = pingport
  waitforconn(ip,pageport,show_status)  

