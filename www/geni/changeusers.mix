include time.repy
include nmclient.repy
include rsa.repy

# needs to be done once...
def initialize_time():
  time_updatetime(34612)


def changeusers(userpubkeylist, nmip, nmport, vesselname, nodepubkey, nodeprivkey):

  try:
    nmhandle = nmclient_createhandle(nmip, nmport)
  except NMClientException:
    return False
  
  myhandleinfo = nmclient_get_handle_info(nmhandle)
  myhandleinfo['publickey'] = nodepubkey
  myhandleinfo['privatekey'] = nodeprivkey
  nmclient_set_handle_info(nmhandle, myhandleinfo)

  # I need to convert the keys to strings before using join
  userpubkeystringlist = []
  for userpubkey in userpubkeylist:
    userpubkeystringlist.append(rsa_publickey_to_string(userpubkey))
    
  # set the users...
  try:
    nmclient_signedsay(nmhandle, "ChangeUsers", myvessel, '|'.join(userpubkeystringlist))
  except NMClientException:
    return False

  return True


