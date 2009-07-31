import deploy_main

# Assorted helper functions that don't really go anywhere else


def dnslookup(ip_or_hostname):
  # ip -> hostname and
  # hostname -> ip
  out, err, retcode = deploy_main.shellexec2('host '+ip_or_hostname)
  # sample strings:
  # 1. [ip] domain name pointer [hostname].
  # 2. [hostname] has address [ip]
  if retcode == 0:
    if out.find('domain name pointer') > -1:
      # this is of type 1, so return the hostname
      hostname = out.split(' ')[-1]
      return hostname.lower()
    elif out.find('has address') > -1:
      # type 2, so return the IP
      ip = out.split(' ')[-1]
      return ip
      # error
    else:
      raise Exception('Error in dnslookup: unexpected return value')
  else:
    if out.find('not found') > -1:
      # probably networkip
      return ip_or_hostname.lower()
    raise Exception('Error in dnslookup ('+str(retcode)+'): '+str(out)+', '+str(err)+' .')

