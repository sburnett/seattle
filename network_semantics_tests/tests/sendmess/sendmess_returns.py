# sendmess returns the number of bytes sent


if callfunc =='initialize':

  x = sendmess('127.0.0.1',12345,"ping")
  if x != 4:
    print 'sendmess did not return correct value'
