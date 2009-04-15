# two openconns should be able to connect to each other.
#  
#
# no expected output


def connection(ip,waitport,waitport2,timeout):
  sock= openconn(ip,waitport,ip,waitport2,timeout)


if callfunc == "initialize":
  ip = '127.0.0.1'
  waitport = 12345
  waitport2 = 23456
 
 

  settimer(0.1,connection,[ip,waitport,waitport2,10])
  sock2 = openconn(ip,waitport2,ip,waitport,timeout=10) 


  
  
  
