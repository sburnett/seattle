# test that an exception occurs if something that is not a commhandle
# is passed to stopcomm




if callfunc == 'initialize':

  for foo in ['string',7]:
    try:
      stopcomm(foo)
    except:
      pass
    else:
      print ' calling stopcomm('+str(foo)+') did not cause exception' 
