"""
Use a mock forwarder to check that the natForwardingLib
behaves correctly when a forwarder immediate returns
False for check conn.

"""

#pragma repy restrictions.normal
#pragma out False

include NatForwardingLib.repy
include mock_forwarder_immediate_response.repy
include NAT_CONSTANTS.repy

if callfunc == 'initialize':
  
  start_mock_for(getmyip(),12346,NAT_NO)
  host_str = getmyip()+':'+str(12347)
  
  print _natforwardinglib_do_check(host_str,getmyip(),12346)
  
  
  stop_mock_for()