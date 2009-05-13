
# test that host name specified for gethostbyname_ex is a string
# or an exception should occur



if callfunc == 'initialize':

  try:
    gethostbyname_ex(7)
  except:
    pass
  else:
    print 'calling gethostbyname(7) did not cause an exception'
