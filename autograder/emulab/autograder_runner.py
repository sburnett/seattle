"""
<Program Name>
  autograder_runner.py 

<Started>
  2/17/2009

<Author>
  Eric Kimbrel, kimbrl@cs.washington.edu

<Purpose>
  The autograder coordinates the running of emulab and a remote seash-like
  interface to execture and grade student project code in a reproduceable and
  controllable environment

  The autograder runs in a continous loop looking for files in the to_grade
  directory.  If files are found it starts an expirament in emulab based on
  the NS file in the TEST_DIR.  Once the emulab expirament is active a remote
  seash like interface is used to execute student code and test cases on seattle
  on emulab nodes.  The output from the nodes is then parsed and graded.  
  The students score is saved ini the STATUS_DIR.

"""


# WARNING the cleanup method curently does NOTHING, so your 
# EMULAB NODES WILL REMAIN RUNNING
import sys
import data_interface
import logging
import time
import remote_emulab
import nm_remote_api
import repyhelper
import thread
import datetime


VERSION = 'beta'

SEATTLE = 'Seattle'  # the name of our project in emulab
ASSIGNMENT_NAME = 'agv1' #emulab exp name

loggerfo = logging.circular_logger('autograder_log')
make_log = True   #logs if true, prints if false
timestamp = datetime.datetime   # used to time stamp log output

grader_state = {}  #hold state about the autograder


## FUNCTIONS TO RUN AND GRADE REPY CODE 


# use a thread to run student code, blocks
# until the code is done executing
def run_student_code(student_file_name,student_file_data,node_dict):   
  print 'running student code'
  try:
    vessels = [node_dict['vessel']]
    results_dict = nm_remote_api.run_on_targets(vessels,
                            student_file_name,student_file_data,
                            student_file_name+' '+node_dict['args'])
  except Exception,e:
    clean_up()
    print(str(e))
    raise
  else:
   #check that all the vessel started
   all_running = True
   for v in vessels:
     (success,info) = results_dict[v]
     if not success: all_running = False
   if not all_running:
      clean_up()
      print("Exception student code failed to start")
      raise Exception, "student code failed to start: "+info
 


# coordinate running code on emulab and processing the output
def run_grader():
   
  # get the list assignemnt test-meta data
  (ns_file_list, ns_file_testsuite_map,test_node_map) = data_interface.get_test_meta_data(ASSIGNMENT_NAME)

  # get the list of student submissions that are ready to grade
  # if the submission isnt in to_grade by this point it will have to wait
  # for the next grade run
  student_submission_list = data_interface.files_to_grade()


  # for this hardcoded case there is only one ns file
  for ns_file in ns_file_list:
    grader_state['current_ns'] = ns_file  #the name of the ns_file is passed around because it is part of the emulab exp name

    # starting emulab
    print "Starting Emulab with toplogy from: "+ns_file

    name_ip_tuples = start_emulab(ns_file)
    
    #hard coded values for troubleshooting with a running instance of emulab
    #name_ip_tuples =  [('node-2.'+ASSIGNMENT_NAME+'wlan.Seattle.emulab.net','10.1.1.2'),('node-1.'+ASSIGNMENT_NAME+'wlan.Seattle.emulab.net','10.1.1.1')]


    
    # initialize the vessels on all emulab nodes
    vessels = init_vessels(name_ip_tuples)   
 
    for student_file in student_submission_list:   
      print '\nRunning tests on '+ns_file+' for '+student_file
    
      # get the list of tests for this topology
      testsuite = ns_file_testsuite_map[ns_file]
      for test_case in testsuite:
        test_mapping = test_node_map[test_case]

        # execute the test_case in emulab (a test case is one test file and one student file for the hardcoded example)
        run_test_on_emulab(student_file,test_mapping,vessels)
     
    #TODO END EMULAB
    print "Terminating emulab with topology from: "+ns_file
    clean_up()

  #Finished grading, mark all student solutions as graded
  for student_file in student_submission_list:   
    data_interface.concat_status_files(student_file)
    data_interface.mark_as_graded(student_file)



# initialize all the vessels in a network topology on emulab
def init_vessels(name_ip_tuples):
  
  
  attempts = 0  

  # creat a list of available hosts
  host_list =[]
  for (host,ip) in name_ip_tuples:
    host_list.append(host)

  print "INTIALIZING HOSTS: "+str(host_list)


  while True:
    # initialize seattle nodes on each host
    try:
      is_init, vessels = nm_remote_api.initialize(host_list, "autograder")
    except Exception,e:
      clean_up()
      print(str(e))
      raise
    else:
      if not is_init:
        if attempts > 2: 
          clean_up()
          print("Exception, failed to initialize seattle nodes "+str(vessels))
          raise Exception, 'failed to intialize seattle nodes '+str(vessels)
        else:
          attempts +=1
          print 'failed to initialize nodes '+str(vessels)
          print 'sleeping for 30 seconds and trying again'
          nm_remote_api.tear_down()
          time.sleep(30)
      else: return vessels 


# execute repy code on emulab nodes
def run_test_on_emulab(filename,test_mapping,vessels): 

  # add the vessel_long_name to the test mapping
  for node_dict in test_mapping:
    found = False    
    #find the vessel that corresponds to this node
    for vessel in vessels:
      if node_dict['node'] in vessel:
        node_dict['vessel'] = vessel
        found = True
        break
    if not found:
      clean_up()
      raise Exception, 'Node specified in test case not found in topology' 

  for node_dict in test_mapping:
    print '\n'
    #get the name and contents of the file to run
    if node_dict['is_student']:
      (file_name,file_data) = data_interface.get_tared_repy_file_data(filename,node_dict['code'])
    else:
      file_name = node_dict['code']
      file_data = data_interface.get_test_content(node_dict['code'])
      
    # run the code in the background?
    if not node_dict['block']:
      thread.start_new_thread(run_student_code,(file_name,file_data,node_dict))
      time.sleep(5)  #give the code time to start
    # run the test so that it blocks
    else:
      testargs =file_name+" "+node_dict['args']
      print("RUNNING TEST "+file_name)

      try:
        results_dict = nm_remote_api.run_on_targets([node_dict['vessel']],file_name,file_data,testargs)
        (test_running,error) = results_dict[node_dict['vessel']]
      except Exception,e:
        clean_up()
        print(str(e))
        #TODO,remove this print
        print "RESULTS DICT "+str(results_dict)
        raise
      else:
        if not test_running:
          if 'timely manner' not in error:
            clean_up()
            raise Exception, "test code "+file_name+"failed to start\n"+error


    # get vessel logs?
    if node_dict['get_logs']:
      try:
        got_it,test_log = nm_remote_api.showlog_vessel(node_dict['vessel'])
      except Exception,e:
        clean_up()
        print(str(e))
        raise
      else:
        if not got_it:
          clean_up()
          print("Exception could not get logs from vessel, error: "+test_log)
          raise Exception, "could not get logs from vessel, error: "+test_log
      

    
      # save the logs
      results = score(test_log,file_name)
      #TODO this method does not exisist
      data_interface.save_output(filename,file_name,results,test_log)




  #reset all vessels before running the next test
  nm_remote_api.reset_targets(vessels)
  time.sleep(3)   #give the vessels a little time

  

 


# call the grade function from the given test
def score(test_log,test_name):
  try:
    repyhelper.translate_and_import(data_interface.TEST_DIR+"/"+test_name)
    results = grade(test_log)
    return test_name+": "+results
  except Exception:
    print("error occured importing grade from "+test_name)
    clean_up()
    raise



## EMULAB REALTED FUNCTIONS

 
# start an expirament in emulab
# blocks for some time waiting for the expirament to go active
def start_emulab(ns_file_name):  
  assign_name = ASSIGNMENT_NAME+grader_state['current_ns'][:-3]

  ns_file_str = data_interface.get_ns_str(ns_file_name)

  print(" parseing ns file")
  # check the ns file for errors
  (passed,message) = remote_emulab.checkNS(ns_file_str)

  if (not passed):
    print(message+"\nException: Failed attempt to parse "+ns_file_name)
    raise Exception, 'Parse of NS file failed'
  
  # start a new exp in non-batchmode
  remote_emulab.startexp(SEATTLE,assign_name,ns_file_str)

  # wait for the exp to go active
  print("waiting for exp to go active")
  remote_emulab.wait_for_active(SEATTLE,assign_name,900)
  
  time.sleep(120) #additional wait for nodes to be ready
  
  # get a mapping of host names to internal ips
  emulab_network_mapping = remote_emulab.get_links(SEATTLE,assign_name)
  host_ip_tuples = remote_emulab.simplify_links(SEATTLE,assign_name
                                                 ,emulab_network_mapping)
  print('assignment running on emulab')

  return host_ip_tuples





## MAIN LOOP AND CLEAN UP


#terminate the expirament in emulab
def clean_up():
  try:
    remote_emulab.endexp(SEATTLE,ASSIGNMENT_NAME+grader_state['current_ns'][:-3])
  except Exception,e:
    print("Exception occured terminating expirament: "+str(e))
    raise
  return


# run a loop waiting for files to grade
def waitforfiles():
  while True:
    # are there files in to_grade?
    if data_interface.files_need_grading():

      print(str(timestamp.now())+' STARTING NEW GRADE RUN')
      
      run_grader()

    #sleep for 10 seconds before looping again
    time.sleep(10)    




if __name__ == "__main__":

  
  # if the -p option is given pring to the console instead of the log
  if len(sys.argv) > 1:  
    if "-p" in sys.argv:
      make_log = False
      print "logging turned off, printing output to console"

  if make_log:
    sys.stdout = loggerfo
    sys.stderr = loggerfo
    
  waitforfiles()

  sys.stdout = logging.flush_logger(sys.stdout)
