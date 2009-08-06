"""
<Program Name> 
  dm_main.py

<Started>
  Jun 22, 2009

<Author>
  Eric Kimbrel


<Purpose>
  Provides a method to deploy a service onto Seattle Geni nodes 

  This program is intended to be run continously so that it can periodically
  check how many forwarders are running and re-deploy forwardrs as nessciary.

  The public and private key of the user running the service must be
  in the current directory.

  Uses a static list of resources provided by a comma seperated file
  WARNING: Ensure there are no spaces at the end of lines in this file.

"""

import sys
import time
import repyhelper

repyhelper.translate_and_import("nmclient.repy")
repyhelper.translate_and_import('rsa.repy')  
  

# TODO add logging

# constants
WAIT_TIME = 180 

XMLRPC_SERVER = 'http://seattlegeni.cs.washington.edu:9001'

# global state
RESOURCE_LIST = []  # a List of dictionaires, each dictionary represents a node
MONITOR_STATE = {}  # dictionary to hold global monitor state,
FAIL_COUNTS = {} # track those nodes that we have faild to contact several times

FAIL_MAX = 5 # number of times we can fail to reach a node before we give up on it


def deploy_on(resources):
# deploys the service on a list of resources
# returns a list of resouces that failed to start
  
  timeout = MONITOR_STATE['timeout']
  
  # read in the file to deploy
  # we read this in every time rather than keeping large files around in memory
  try:
    file_obj = open(MONITOR_STATE['file_name'])
    file_str = file_obj.read()
  except Exception, e:
    print 'ERROR: could not open file: '+str(e)
    global_cleanup()
  else:
    file_obj.close()

  good_list = []
  bad_list = []  

  
  # deploy the service on each node,
  for node in resources:
    try:
      service_running = False

      # use nmclient calls to launch each forwarder
      print 'INFO: deploying on '+node['node_ip']
  
      # get the vessel to use...
      myvessel = node['vessel_id']
    
    
      # create a node handle
      nmhandle = nmclient_createhandle(node['node_ip'],node['node_port'],
                                       timeout=timeout)
      node['nmhandle'] = nmhandle

      # set keys
      myhandleinfo = nmclient_get_handle_info(nmhandle)  
      myhandleinfo['publickey'] = MONITOR_STATE['pubkey']
      myhandleinfo['privatekey'] =MONITOR_STATE['privatekey']
      nmclient_set_handle_info(nmhandle,myhandleinfo)
    
      # reset the vessel 
      nmclient_signedsay(nmhandle, "ResetVessel", myvessel)

      # get information about the vessels...
      vesselinfo = nmclient_getvesseldict(nmhandle)

        
      # stop the vessel if it is running (it shouldnt be)
      if vesselinfo['vessels'][myvessel]['status'] == 'Started':
        nmclient_signedsay(nmhandle, "StopVessel", myvessel)
        time.sleep(1) # allow the vessel to stop
        vesselinfo = nmclient_getvesseldict(nmhandle)
        if vesselinfo['vessels'][myvessel]['status'] == 'Started':
          #there is something wrong with this node so just release it
          print 'ERROR: node could not be reset: '+str(node)
        
        
    
      # add the file to the vessel
      nmclient_signedsay(nmhandle, "AddFileToVessel", myvessel,
                       MONITOR_STATE['file_name'],""+file_str+"")

    
      # start the vessel
      nmclient_signedsay(nmhandle, "StartVessel", myvessel,
                       MONITOR_STATE['file_name']+" "+MONITOR_STATE['file_args'])
      time.sleep(1)
    

      #check the vessel status
      vesselinfo = nmclient_getvesseldict(nmhandle)
      if vesselinfo['vessels'][myvessel]['status'] == 'Started':
        good_list.append(node)
      else:
        bad_list.append(node)
        print 'ERROR": vessel shoud be Started but is '+  vesselinfo['vessels'][myvessel]['status']
    except Exception, e:
      print 'ERROR: '+str(e)
      bad_list.append(node)
      print 'ERROR: FAILED to start service on vessel: '+node['node_ip']+':'+node['vessel_id']
 
    
  return bad_list
  

  
def detect_failures():
  # returns a list of nodes that are not running
  fail_list = []
  for node in RESOURCE_LIST:
    try:
      # get information about the vessels...
      vesselinfo = nmclient_getvesseldict(node['nmhandle'])

      # if the vessel status isnt started it must have failed
      status = vesselinfo['vessels'][node['vessel_id']]['status'] 
      if status != 'Started':
        fail_list.append(node)
        print 'ERROR: vessel status reported as '+status+' for node: '+str(node)
  
    except Exception, e:
      print 'ERROR: could not get vessel info: '+str(e)
      fail_list.append(node)

  #do application specific check
  if 'extension' in MONITOR_STATE:
    addition_failures = MONITOR_STATE['extension'].ext_detect_failures(RESOURCE_LIST)
    if len(addition_failures > 0):
      for node in addition_failues:
        if node not in fail_list:
          fail_list.append(node)

  return fail_list 



def increment_failure(list):
# increments the failure count of each node in list
# if fail count = FAIL_MAX the node is removed from the list 
# or resources.
# 
# when the resource list is empty exit this program
  for node in list:
    key = node['node_ip']+node['vessel_id']
    FAIL_COUNTS[key] += 1
    if FAIL_COUNTS[key] > FAIL_MAX:
      RESOURCE_LIST.remove(node)
      del FAIL_COUNTS[key]
      print 'ERROR: The following resource can not be reached. '+str(node)
    
  if len(RESOURCE_LIST) < 1:
    print 'ERROR: All resources have failed, doing harsh exit'
    sys.exit() 


def filter_failures(bad_list):
  # return a new list that only contains
  # items that are in bad_list and RESOURCE_LIST
  
  ret_list = []
  for node in bad_list:
    if node in RESOURCE_LIST:
      ret_list.append(node)

  return ret_list


def remove_duplicates(list):
  ret_list = []
  for thing in list:
    if thing not in ret_list:
      ret_list.append(thing)

  return ret_list




def main():
# run a loop forever re-deploying services
# if there is a failure

  #TODO change to logging
  print 'INFO: Deployment manager started.'

  # these arent really bad, im just setting up for the loop
  bad_list = RESOURCE_LIST 
  

  while True:
    # deploy the service
    if len(bad_list) > 0:
      bad_list = deploy_on(bad_list)
    
    # wait for some times and then check the service
    time.sleep(WAIT_TIME)
       
    # get a list of the resources that have stopped running
    bad_list.extend(detect_failures())
    bad_list = remove_duplicates(bad_list)
    increment_failure(bad_list)

    # remove nodes that have failed too many times
    bad_list = filter_failures(bad_list)

    


            
    

if __name__ == "__main__":
# setup global state and check command line arguments  

  time_updatetime(34612)  

  # check the number of call arguments
  if len(sys.argv) < 5 or len(sys.argv) > 6:
    print 'USAGE: <username> <file_name to deploy> <program args> <resource file> | <timeout> |' 
    sys.exit()
  
  # set the optional timeout argument if it was supplied
  elif len(sys.argv) == 6:
    MONITOR_STATE['timeout'] = int(sys.argv[5])
  else:
    MONITOR_STATE['timeout'] = 30 # 30seconds default

  username = sys.argv[1]
  MONITOR_STATE['file_name'] = sys.argv[2]
  MONITOR_STATE['file_args'] = sys.argv[3]

  # ensure the file exists, don't read it in, because we don't need to
  # keep it in memory forever
  try:
    file_obj = open(MONITOR_STATE['file_name'])
  except Exception, e:
    print 'ERROR: could not open file: '+str(e)
    sys.exit()
  else:
    file_obj.close()
  
  # read in public and private keys for the user
  key_file = open(username+".publickey")
  pubkey = key_file.read()
  key_file.close()
  key_file = open(username+".privatekey")
  privatekey = key_file.read()
  key_file.close()
  MONITOR_STATE['pubkey'] = rsa_string_to_publickey(pubkey)
  MONITOR_STATE['privatekey'] = rsa_string_to_privatekey(privatekey)
  
  # read in resources
  file_obj = open(sys.argv[4])
  lines = file_obj.readlines()
  file_obj.close()
  for nextline in lines:
    nextline = nextline[:-1] #remove \n
    (ip,port,vid) = nextline.split(',')
    RESOURCE_LIST.append({'node_ip':ip,'node_port':int(port),'vessel_id':vid})  
  

  # set the initial FAIL_COUNTS
  for node in RESOURCE_LIST:
    #use the ip and vessel id as a key
    FAIL_COUNTS[node['node_ip']+node['vessel_id']] = 0

  main()



  


	
	
	
	
	
	
	
	
	
	
	
	

	
