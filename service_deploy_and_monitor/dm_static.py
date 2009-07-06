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

  Uses a static list of hardcoded resources, this will be replaced by
  a dynamic program in the future

  
  
  EXTENSIONS: THis program can optionally include one extension that performs a
  application specific check.  The extension name is entered on the command line
  and the extension contangs two methods

    ext_setup() # sets up any nessicary state for the extension
    ext_detect_failues(RESOURCE_LIST) # returns a list of failed nodes (see detect_failures())

"""

import sys

import time
import repyhelper


# TODO xml rpc faults
# TODO add logging

# constants
WAIT_TIME = 60 # TODO, bump this way up, maybe every 10 minutes? 

XMLRPC_SERVER = 'http://seattlegeni.cs.washington.edu:9001'

# global state
RESOURCE_LIST = []  # a List of dictionaires, each dictionary represents a node
MONITOR_STATE = {}  # dictionary to hold global monitor state,





def deploy_on(resources):
  
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

    
  # deploy the service on each node,
  for node in resources:
    try:
      service_running = False

      # use nmclient calls to launch each forwarder
      print 'INFO: deploying on '+node['node_ip']
  
      # get the vessel to use...
      myvessel = node['vessel_id']
    
    
      # create a node handle
      nmhandle = nmclient_createhandle(node['node_ip'],node['node_port'],timeout=30)
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
        service_running = True
      else:
        print 'ERROR": vessel shoud be Started but is '+  vesselinfo['vessels'][myvessel]['status']
    except Exception, e:
      print 'ERROR: '+str(e)
      server_running = False  

    
    # add the node to resource dict  
    if not service_running: 
      print 'ERROR: FAILED to start service on vessel: '+node['node_ip']+':'+node['vessel_id']
 
    
  
  
  
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




def main():
# run a loop forever re-deploying services on new resources
# if there is a failure

  #TODO change to logging
  print 'INFO: Forwarder deployment manager started.'

  deploy_on(RESOURCE_LIST)
  
  while True:
  
    time.sleep(WAIT_TIME)
   
        
    # get a list of the resources that have stopped running
    failed_resources = detect_failures()

    if len(failed_resources) > 0:

      #TODO change to logging
      print 'ERROR: '+str(len(failed_resources))+' have failed: '
      print 'trying to restart'
      deploy_on(failed_resources)


            
    

if __name__ == "__main__":
# setup global state and check command line arguments  

  # for node manager interaction
  repyhelper.translate_and_import("nmclient.repy")
  repyhelper.translate_and_import('rsa.repy')  
  

  #TODO how do we decided what port to use for this?
  # we need the ntp time for signed comms with a nodemanager
  time_updatetime(34612)  

  # check the number of call arguments
  if len(sys.argv) != 4 and len(sys.argv) != 5:
    print 'USAGE: <username> <file_name to deploy> <program args> |<extension module name, for example: dm_foo_ext> |'
    sys.exit()

  
  MONITOR_STATE['file_name'] = sys.argv[2]
  # ensure the file exists
  try:
    file_obj = open(MONITOR_STATE['file_name'])
  except Exception, e:
    print 'ERROR: could not open file: '+str(e)
    sys.exit()
  else:
    file_obj.close()
  
  MONITOR_STATE['file_args'] = sys.argv[3]

  
  key_file = open(sys.argv[1]+".publickey")
  pubkey = key_file.read()
  key_file.close()

  key_file = open(sys.argv[1]+".privatekey")
  privatekey = key_file.read()
  key_file.close()
  
  #convert the key strings to key dicts
  MONITOR_STATE['pubkey'] = rsa_string_to_publickey(pubkey)
  MONITOR_STATE['privatekey'] = rsa_string_to_privatekey(privatekey)
  
  
  # if an extension was specified on the command line bring it in
  if len(sys.argv) == 5:
    MONITOR_STATE['extension'] = __import__(sys.argv[4])
    MONITOR_STATE['extension'].ext_setup() #setup extension state



  #statically set the resource list
  RESOURCE_LIST.append({'node_ip':'128.111.52.63','node_port':1224,'vessel_id':'v26'})
  RESOURCE_LIST.append({'node_ip':'128.42.142.43','node_port':1224,'vessel_id':'v26'})
  RESOURCE_LIST.append({'node_ip':'143.107.111.234','node_port':1224,'vessel_id':'v30'})
  RESOURCE_LIST.append({'node_ip':'128.112.139.108','node_port':1224,'vessel_id':'v32'})
  RESOURCE_LIST.append({'node_ip':'212.201.44.82','node_port':1224,'vessel_id':'v17'})
  RESOURCE_LIST.append({'node_ip':'128.2.223.64','node_port':1224,'vessel_id':'v30'})
  RESOURCE_LIST.append({'node_ip':'72.36.112.72','node_port':1224,'vessel_id':'v75'})
  RESOURCE_LIST.append({'node_ip':'194.117.20.214','node_port':1224,'vessel_id':'v12'})
  RESOURCE_LIST.append({'node_ip':'133.11.240.57','node_port':1224,'vessel_id':'v34'})
  RESOURCE_LIST.append({'node_ip':'129.24.211.29','node_port':1224,'vessel_id':'v31'})



  main()
  


	
	
	

	
