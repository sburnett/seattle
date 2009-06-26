# Tests to make sure that time_server.repy is announcing itself properly
# to the central server over a period of 15 minutes (because time_server.repy
# re-announces itself every four to five minutes.


include centralizedadvertise.repy


if callfunc == "initialize":

  if len(callargs) > 1:
    raise Exception("Too many call arguments")

  elif len(callargs) == 1:
    port = int(callargs[0])
    ip = getmyip()

  else:
    raise Exception("Need port number")

  print "This test performs a series of 15 tests to make sure the service time_server.repy is properly, and continually, announcing to the central server"

  success = True
  print "Performing test 1 :"
  for x in range(2,17):
    while True:
      try:
        ipandport = centralizedadvertise_lookup("time_server")
      except Exception,e:
        if "Interrupted system call" in str(e):
          print "Interrupted system call, retrying test..."
        else:
          print "TEST FAILED on try ",x-1,": ",e
          print "Performing test ",x,":"
          success = False
          break
      else:
        print "time_server.repy successfully announced the following ip and port:"
        print "remote ip: ",ipandport[0]
        print "remote port: ",ipandport[1]
        print "Test ",x-1," complete"
        if x != 16:
          print "Performing test ",x,":"
          sleep(60)
        break

  if success:
    print "All tests succeeded!"
