"""

Manually connecto to a forwarder and see that we get the right response for
check behind nat

This tests verifies that the forwarder behaves correctly,
other tests verify that the library behaves correctly.


"""

#pragma repy restrictions.normal

include NAT_CONSTANTS.repy
include session.repy


def nothing(rip,rport,sock,th,lh):
  sock.close()


if callfunc == 'initialize':

  fip = "198.133.224.147"
  fport = 63169

  myip = "128.208.4.224"

  # PART 1, check answer when ips don't match

  
  sock = openconn(fip,fport)
  sock.send(NAT_CHECK_CONN) # tells the forwrader we want to check behind nat
 
  #send my ip, this should be what the other end sees
  session_sendmessage(sock,'999.99.99:12347')


  msg = session_recvmessage(sock)
  if msg != NAT_YES:
    raise Exception("GOT WRONG ANWER IN PART 1: "+msg)

  sock.close()
  
  # PART 2, ips match but no connection can be made

  sock = openconn(fip,fport)
  sock.send(NAT_CHECK_CONN) # tells the forwrader we want to check behind nat
 
  #send my ip, this should be what the other end sees
  session_sendmessage(sock, myip + ':12347')

  
  msg = session_recvmessage(sock)
  if msg != NAT_CHECK_CONN:
    raise Exception('not asked to check conn in part 2 '+msg)

  # tell the server we are ready
  session_sendmessage(sock,NAT_YES)


  msg = session_recvmessage(sock)
  if msg != NAT_YES:
    raise Exception("GOT WRONG ANWER IN PART 2: "+msg)

  sock.close()


  # part 3, ips match and connection can be made

  
  sock = openconn(fip,fport)
  sock.send(NAT_CHECK_CONN) # tells the forwrader we want to check behind nat
 
  #send my ip, this should be what the other end sees
  session_sendmessage(sock, myip+':12347')
  
  msg = session_recvmessage(sock)
  if msg != NAT_CHECK_CONN:
    raise Exception('not asked to check conn in part 3 '+msg)

  handle = waitforconn(myip,12347,nothing)

  # tell the server we are ready
  session_sendmessage(sock,NAT_YES)


  msg = session_recvmessage(sock)
  if msg != NAT_NO:
    raise Exception("GOT WRONG ANWER IN PART 3: "+msg)

  stopcomm(handle)

  sock.close()
  
  print "Passed"
