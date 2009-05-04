# A call to getmyip() when not connected to the network will 
# cause an exception
#
# RUN THIS TEST WHILE NOT ON A NETWORK

if callfunc == 'initialize':
  
  try:
    getmyip()
  except:
    pass
  else:
    print 'no exception occured'
