"""
<Program Name> 
  dm_main.py

<Started>
  Jun 22, 2009

<Author>
  Eric Kimbrel


<Purpose>
  Provides a method to deploy a service onto Seattle Geni nodes (using the
  seattle geni xml-rpc interface). Takes the number of instances to deploy 
  as a command line argument. Uses the servce logger to keep a log of deployments.

  This program is intended to be run continously so that it can periodically
  check how many forwarders are running and re-deploy forwardrs as nessciary.

  Whenever a node is seen as not running, that node is released, a new node
  is acquired, and the service is restarted on the new node.

  This program will hault if a problem occurs with the Geni xml-rpc interface

  NOTE: This assumes we want only routeable nodes so nodes that are advertised as
  $NAT.... will be rejected. THIS PROGRAM NEEDS UPDATED IF THE WAY NAT NODES ARE
  IDENTIFIED IS UPDATED

  EXTENSIONS: THis program can optionally include one extension that performs a
  application specific check.  The extension name is entered on the command line
  and the extension contangs two methods

    ext_setup() # sets up any nessicary state for the extension
    ext_detect_failues(RESOURCE_LIST) # returns a list of failed nodes (see detect_failures())

"""

import sys
import geni_xmlrpc_clientlib 
import time
import repyhelper


# TODO xml rpc faults
# TODO add logging

# constants
WAIT_TIME = 30 # TODO, bump this way up, maybe every 10 minutes? 
DEPLOY_INTERVAL = 10 #TODO bump this up to a few minutes, something > WAIT_TIME
XMLRPC_SERVER = 'http://seattlegeni.cs.washington.edu:9001'

# global state
RESOURCE_LIST = []  # a List of dictionaires, each dictionary represents a node
MONITOR_STATE = {}  # dictionary to hold global monitor state,




def acquire_resources(number_of_resources):
# wrapper to abstract the network communications
# exits the program if this fails
# rejects non-public nodes
# NOTE: this method may return fewer resources than requested

  try:
    resource_list = MONITOR_STATE['xmlrpc'].acquire_wan_resources(number_of_resources)
  except Exception, e:
    print 'ERROR: failed to acquire new resources, exception occured: '+str(e)
    global_cleanup()
  else:
    print 'INFO: acquired '+str(len(resource_list))+' resources:\n    '+str(resource_list)
  
  # reject nodes that are advertised as not pulbically reachable
  reject_list =[]
  for node in resource_list:
    if 'NAT$' in node['node_ip']: reject_list.append(node)
  
  for node in reject_list:
    resource_list.remove(node)

  return resource_list


def release_resouces(handle_list):
# wrapper to abstract the network communications
# exits the program if this fails 
  try:
    MONITOR_STATE['xmlrpc'].release_resources(handle_list)
  except:
    #TODO change to logging
    print 'ERROR: failed to release resources, terminating to prevent further resource leak'
    sys.exit()
  else:
    print 'INFO: released failed resources.'
    


def get_nodes_and_deploy(number_of_resources):
  # get a number of resources and deploy the service on each one   
  node_dict = acquire_resources(number_of_resources)
 

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
  release_list = [] 
  for node in node_dict:
    service_running = False

    # use nmclient calls to launch each forwarder
    print 'INFO: deploying on '+str(node)
  
    # get the vessel to use...
    myvessel = node['vessel_id']
    
    
    # create a node handle
    nmhandle = nmclient_createhandle(node['node_ip'],node['node_port'])

    # set keys
    myhandleinfo = nmclient_get_handle_info(nmhandle)  
    myhandleinfo['publickey'] = MONITOR_STATE['pubkey']
    myhandleinfo['privatekey'] =MONITOR_STATE['privatekey']
    nmclient_set_handle_info(nmhandle,myhandleinfo)
    

    # get information about the vessels...
    vesselinfo = nmclient_getvesseldict(nmhandle)

        
    # stop the vessel if it is running (it shouldnt be)
    if vesselinfo['vessels'][myvessel]['status'] == 'Started':
      nmclient_signedsay(nmhandle, "StopVessel", myvessel)
      time.sleep(1) # allow the vessel to stop
      vesselinfo = nmclient_getvesseldict(nmhandle)
      if vesselinfo['vessels'][myvessel]['status'] == 'Started':
        #there is something wrong with this node so just release it
        print 'INFO: node could not be reset: '+str(node)
        release_list.append(node)
        
    
    # add the file to the vessel
    nmclient_signedsay(nmhandle, "AddFileToVessel", myvessel,
                       MONITOR_STATE['file_name'],"""print 'hello'""")

    
    # start the vessel
    nmclient_signedsay(nmhandle, "StartVessel", myvessel,
                       MONITOR_STATE['file_name'])
    time.sleep(1)

    

    #check the vessel status
    vesselinfo = nmclient_getvesseldict(nmhandle)
    if vesselinfo['vessels'][myvessel]['status'] != 'Started':
      service_running = True

    
    # add the node to resource dict  
    if service_running: 
      RESOURCE_LIST.append(node)
      print 'INFO: started service on new vessel: '+node['node_ip']+':'+node['vessel_id']
    else: 
      release_list.append(node) #release resources that failed to start
      print 'INFO: FAILED to start service on new vessel: '+node['node_ip']+':'+node['vessel_id']
 
    
  # release faild resources
  release_resources(release_list)
  
  print 'EXITED GET AND DEPLOY'

def detect_failures():
  # returns a list of nodes that are not running

  fail_list = []
  for node in RESOURCE_LIST:
  
    # get information about the vessels...
    vesselinfo = nmclient_getvesseldict(node['handle'])

    # if the vessel status isnt started it must have failed
    status = vesselinfo['vessels'][node['vessel_id']]['status'] 
    if status != 'Started':
      fail_list.append(node)
      print 'INFO: vessel status reported as '+status+' for node: '+str(node)
  
  #do application specific check
  if 'extension' in MONITOR_STATE:
    addition_failures = MONITOR_STATE['extension'].ext_detect_failures(RESOURCE_LIST)
    if len(addition_failures > 0):
      for node in addition_failues:
        if node not in fail_list:
          fail_list.append(node)

  return fail_list 


def global_cleanup():
# release any resources still being held
  print "RUNNING GLOBAL CLEAN UP"
  failed_handles = [] 
  for node in RESOURCE_LIST:
    failed_handles.append[node['handle']]
  try:
    release_resources(failed_handles)
  finally:
    sys.exit()



def main():
# run a loop forever re-deploying services on new resources
# if there is a failure

  #TODO change to logging
  print 'INFO: Forwarder deployment manager started.'

  # stagger the initial deployment onto nodes to esnure
  # that all of the resources don't expire at the same time
  if MONITOR_STATE['num_services_request'] > 1:
    total = MONITOR_STATE['num_services_request']
    first_half = total / 2
    second_half = total - first_half
    get_nodes_and_deploy(first_half)
    time.sleep(DEPLOY_INTERVAL)
    get_nodes_and_deploy(second_half)
  else:
    get_nodes_and_deploy(MONITOR_STATE['num_services_request'])
  
  while True:
  
    time.sleep(WAIT_TIME)
   
        
    # get a list of the resources that have stopped running
    failed_resources = detect_failures()

    if len(failed_resources) > 0:

      #TODO change to logging
      print 'INFO: '+str(len(failed_resources))+' have failed: '+str(failed_resources)

      # get the handles for each failed resource
      failed_handles = []
      for node in failed_resources:
        failed_handles.append[node['handle']]
        RESOURCE_LIST.remove(node) # remove failed resources from the dict

      release_resources(failed_handles)
      
    # replace the failed resources
    new_resources_needed = MONITOR_STATE['num_services_request'] - len(RESOURCE_LIST)
    get_nodes_and_deploy(new_resources_needed)




if __name__ == "__main__":
# setup global state and check command line arguments  

  # for node manager interaction
  repyhelper.translate_and_import("nmclient.repy")
  repyhelper.translate_and_import('rsa.repy')  


  #TODO how do we decided what port to use for this?
  # we need the ntp time for signed comms with a nodemanager
  time_updatetime(34612)  

  # check the number of call arguments
  if len(sys.argv) != 5 and len(sys.argv) != 6:
    print 'USAGE: <geni_user> <geni password> <file_name to deploy> <number of instances to deploy> |<extension module name, for example: dm_foo_ext> |'
    sys.exit()

  #TODO check that the geni_user is valid ?
  MONITOR_STATE['geni_user'] = {'username':sys.argv[1],'authstring':sys.argv[2]}


  MONITOR_STATE['file_name'] = sys.argv[3]
  # ensure the file exists
  try:
    file_obj = open(MONITOR_STATE['file_name'])
  except Exception, e:
    print 'ERROR: could not open file: '+str(e)
    sys.exit()
  else:
    file_obj.close()
  
  # ensure the number of services to deploy is an int
  try:
    MONITOR_STATE['num_services_request'] = int(sys.argv[4])
  except:
    print 'ERROR: number of forwarders entered must be an int'
    sys.exit()

  # set up the connection to the xmlrpc_server
  try:
    MONITOR_STATE['xmlrpc'] = geni_xmlrpc_clientlib.client(username=sys.argv[1],
               authstring=sys.argv[2], allow_ssl_insecure=True)

    MONITOR_STATE['xmlrpc'].warmup()
  except:
    print 'ERROR: could not make a connection to: '+XMLRPC_SERVER 
    sys.exit()

  pubkey = MONITOR_STATE['xmlrpc'].get_public_key()
  #MONITOR_STATE['privatekey'] = MONITOR_STATE['xmlrpc'].get_private_key()
  #TODO get the private key from a local file because the method seems broken
  key_file = open(sys.argv[1]+".privatekey")
  privatekey = key_file.read()
  key_file.close()
  
  #convert the key strings to key dicts
  MONITOR_STATE['pubkey'] = rsa_string_to_publickey(pubkey)
  MONITOR_STATE['privatekey'] = rsa_string_to_privatekey(privatekey)
  
  
  # if an extension was specified on the command line bring it in
  if len(sys.argv) == 6:
    MONITOR_STATE['extension'] = __import__(sys.argv[5])
    MONITOR_STATE['extension'].ext_setup() #setup extension state


  wrap the main method with a try except to clean_up resources
  try:
    main()
  except Exception, e:
    raise e
  finally:
    global_cleanup()


  
