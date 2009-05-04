# if a host name that cannot be resolved is used an exception occurs.



if callfunc == 'initialize':


  port = 12345

  try:
    sendmess('notactuallyahost',port,'ping')
  except:
    pass
  else:
    print "using 'notactuallyahost' did not cause exception"
  

  
