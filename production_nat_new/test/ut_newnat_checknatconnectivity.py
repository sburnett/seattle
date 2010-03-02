include CheckConnectivity.repy

#pragma repy restrictions.normal

if callfunc == 'initialize':

  print checkconnectivity_isBidirectional(getmyip(),12347)
