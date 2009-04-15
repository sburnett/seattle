# if openconn is performed when there is no listener waiting for the
# connection an exception is thrown
#
# no expected output

if callfunc == "initialize":

  ip = '127.0.0.1'
  waitport = 12345
 
  try:
    sock = openconn(ip,waitport,ip,23456)
  except Exception:
    pass
  else:
    sock.close()
    print "ERROR, openconn with no listener did not throw exception"
