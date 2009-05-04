# a call to gethostbyname_ex with an invalid host name will 
# cause an exception


if callfunc == 'initialize':

  host = 'Thisaddressdoesnotexist'

  try:  
    (one,two,three) = gethostbyname_ex(host)
  except:
    pass
  else:
    print 'no exception caused be invalid host name'
