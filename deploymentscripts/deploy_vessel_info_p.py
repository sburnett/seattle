"""
<Program Name>
  deploy_vessel_info_p.py

<Started>
  July 2009

<Author>
  n2k8000@u.washington.edu
  Konstantin Pik

<Purpose>
  This file takes care of quering the servers to which our nodes advertise to, and then
  based on what is advertised it diff's it with the iplist2.list file and reports how many
  nodes are not checked (aka "other" nodes).
  
  Three files are written on a successfull run:
  
  advertised_nodes_uniq.list:
    The list of the uniq nodes (nodes not in the iplist2.list file).
    
  advertised_nodes_list.list
    The list of all the nodes advertised
    
  advertised_nodes_rdns.list:
    The list of all the nodes that have been reverse dns looked up.
"""

import repyhelper
import os
import deploy_main
import deploy_helper
import parallelize_repy

print 'Import .repy files into namespace...',
# make sure we have access to the rsa lib in the local namespace
repyhelper.translate_and_import('rsa.repy')
repyhelper.translate_and_import('advertise.repy')
print 'Done'





print 'Loading keys from files...',
canonicalpublickey = rsa_file_to_publickey("canonical.publickey")

v2publickey = rsa_file_to_publickey("v2.publickey")

# The key used for new donations...
acceptdonationpublickey = rsa_file_to_publickey("acceptdonation.publickey")

# Used for our first attempt at doing something sensible...
movingtoonepercentpublickey = rsa_file_to_publickey("movingtoonepercent.publickey")
onepercentpublickey = rsa_file_to_publickey("onepercent.publickey")

# Used as the second onepercentpublickey -- used to correct ivan's
# mistake of deleting vesselport entries from the geni database
movingtoonepercent2publickey = rsa_file_to_publickey("movingtoonepercent2.publickey")
onepercent2publickey = rsa_file_to_publickey("onepercent2.publickey")


# Getting us out of the mess we started with
#genilookuppublickey = rsa_file_to_publickey("genilookup.publickey")
movingtogenilookuppublickey = rsa_file_to_publickey("movingtogenilookup.publickey")

# Used as the many events onepercent publickey -- This has 50 events per vessel
movingtoonepercentmanyeventspublickey = rsa_file_to_publickey("movingtoonepercentmanyevents.publickey")
onepercentmanyeventspublickey = rsa_file_to_publickey("onepercentmanyevents.publickey")

knownstates = [canonicalpublickey, acceptdonationpublickey, 
           movingtoonepercentpublickey, onepercentpublickey,
           movingtoonepercent2publickey, onepercent2publickey,
           movingtoonepercentmanyeventspublickey, onepercentmanyeventspublickey,
           movingtogenilookuppublickey, v2publickey]

# string representations of the above states
knownstates_string_representation = ['canonicalpublickey', 'acceptdonationpublickey', 
           'movingtoonepercentpublickey', 'onepercentpublickey',
           'movingtoonepercent2publickey', 'onepercent2publickey',
           'movingtoonepercentmanyeventspublickey', 'onepercentmanyeventspublickey',
           'movingtogenilookuppublickey', 'v2']

print 'Done'


def main():

  # delete the old advertised_nodes_list.list file
  try:
    os.remove('advertised_nodes_list.list')  
  except OSError, ose:
    pass
  except Exception, e:
    print e
    return
  
  advertised_nodes_list = []
  
  # enumerate through each key we have
  for i in range(len(knownstates)):
    current_key = knownstates[i]
    print 'Nodes corresponding to '+knownstates_string_representation[i]+'...',
    
    # query for all the nodes we have 
    nodes_in_state = advertise_lookup(current_key, 10000000)
    
    # this is the counter for the number of nodes in that state
    total_counter = 0
    try:
      # write all of these nodes to file
      advertised_nodes_handle = open('advertised_nodes_list.list', 'a')
      
      # write the type of nodes these are as a comment
      advertised_nodes_handle.write('\n\n# '+knownstates_string_representation[i])
      print 'writing to file...',
      
      counter = 0
      total_counter += counter
      for each_node in nodes_in_state:
        # strip the :port from each node, make sure it's not an empty string
        if each_node:
          nodeip, sep, port = each_node.rpartition(':')
          advertised_nodes_list.append(nodeip)
          advertised_nodes_handle.write('\n'+str(nodeip))
          counter += 1
      advertised_nodes_handle.write('\n\tA total of '+str(counter))
      advertised_nodes_handle.close()
      print 'Finished'
      
    except Exception, e:
      print 'An error occured while writing to file ('+str(e)+')'
  
  # this makes it uniq
  advertised_nodes_list = list(set(advertised_nodes_list))
  if not advertised_nodes_list:
    print "You've hit a timeout with the server, it thinks you're spamming it. Please wait"
    return
  print advertised_nodes_list
  
  
  
  # now we read in the other iplist file, ignore all !user: lines and comments
  # just use the method from deploy_main to do that, but it'll return an array
  # of tuples (user, hostname/ip) so we'll just grab the hostname/ip field
  remote_host_tuples = deploy_main.get_remote_hosts_from_file('iplist2.list', True)
  
  # this'll keep track of the actual hostnames/ips
  pl_nodes = []

  for each_host in remote_host_tuples:
    # each_host[0]: username
    # each_host[1]: hostname/ip
    pl_nodes.append(each_host[1])
    
  # keeps track of ip->hostname and hostname->ip mappings
  dns_dict = {}
  
  # this'll keep track of the already checked nodes
  dns_dict['flagged'] = []
  
  # keeps track of the rerversed dns entries
  advertise_reversedns = []
  
  # loopbacks, network, eg: 192.*
  networkiplist = []

  # start multiple threads to reverse lookup all the hostnames/ips as our iplist2.list file 
  # might have mixed forms (1.1.1.1 <-> bla.foo.bar, and we have to match those up)
  func_handle = parallelize_repy.parallelize_initfunction(advertised_nodes_list, deploy_helper.dnslookup, 15)
  while not parallelize_repy.parallelize_isfunctionfinished(func_handle):
    time.sleep(1)
    
  # Function is done
  results_dict = parallelize_repy.parallelize_getresults(func_handle)
  for each_key in results_dict.keys():
    print results_dict[each_key]
    
  for each_tuple in results_dict['returned']:
    iphostname = each_tuple[0]
    reverse_iphostname = each_tuple[1]
    
    print str(iphostname)+' resolves to '+reverse_iphostname
    
    if iphostname == reverse_iphostname:
      networkiplist.append(iphostname)
    else:
      dns_dict[iphostname] = reverse_iphostname
      dns_dict[reverse_iphostname] = iphostname
      advertise_reversedns.append(reverse_iphostname)
  
  try:
    # write the reverse dns's looked up
    reversed_filehandle = open('advertised_nodes_rdns.list', 'w+')
    for each_host in advertise_reversedns:
      reversed_filehandle.write('\n'+each_host)
    reversed_filehandle.close()
  except Exception, e:
    print e
    
  # combine the two lists
  all_advertised_nodes = advertise_reversedns + advertised_nodes_list
  
  uniq_counter = 0
  uniq_list = []
  
  print '\n\n'
  
  for each_node in all_advertised_nodes:
    # make sure this node isn't flagged as already checked
    try:
      if each_node not in dns_dict['flagged']:
        if each_node not in pl_nodes:
          # make sure the reversedns counterpart isn't in the list either
          if dns_dict[each_node] not in pl_nodes:
            uniq_counter += 1
            print each_node+' is not in pl_list'
            uniq_list.append(each_node)
            # flag it as already checked
        # flag the node's counterpart as checked
        dns_dict['flagged'].append(dns_dict[each_node])
    except KeyError, ke:
      # key error means it's an ip in the networkiplist
      uniq_counter += 1
      print each_node+' is not in pl_list (ke)'
      uniq_list.append(each_node)
    except Exception, e:
      print e
  
  try:
    # write the reverse dns's looked up
    uniq_filehandle = open('advertised_nodes_uniq.list', 'w+')
    for each_host in uniq_list:
      uniq_filehandle.write('\n'+each_host)
    uniq_filehandle.close()
  except Exception, e:
    print e
  
  print '\n\n'
  print 'The following files were created: advertised_nodes_uniq.list, advertised_nodes_list.list, and advertised_nodes_rdns.list'
  print 'The number of non-PL/University nodes is '+str(uniq_counter) 
  
  
    
if __name__ == '__main__':
  main()

