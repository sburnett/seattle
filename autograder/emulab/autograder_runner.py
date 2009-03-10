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
ASSIGNMENT_NAME = 'webserverlive' #emulab exp name

log = logging.circular_logger('autograder_log')
make_log = True   #logs if true, prints if false


## FUNCTIONS TO RUN AND GRADE REPY CODE 


# use a thread to run student code, blocks
# until the code is done executing
def run_student_code(vessels,student_file_name,student_file_data):   
  try:
    webserver_running,error = nm_remote_api.run_on_targets(vessels,
                            student_file_name,student_file_data,
                            student_file_name+' 63173')
  except Exception,e:
    clean_up()
    my_print(str(e))
    raise
  else:
    if not webserver_running:
      clean_up()
      my_print("Exception student code failed to start")
      raise Exception, "student code failed to start: "+error
 


# coordinate running code on emulab and processing the output
def grade_it(name_ip_tuples):

  while data_interface.files_need_grading():

    file_to_grade = data_interface.next_file_to_grade()

    my_print("grading "+file_to_grade)

    data_interface.mark_in_progress(file_to_grade)    

    # execute the assignment and tests in emulab
    run_webserver_tests(file_to_grade,name_ip_tuples)



# execute repy code on emulab nodes
def run_webserver_tests(filename,name_ip_tuples): 

  # get a tuple for each test [(filename,file_content_str)...]
  test_tuples = data_interface.get_tests()

  #get list of hosts
  host_list =[]
  for (host,ip) in name_ip_tuples:
    host_list.append(host)
 
  # initialize seattle nodes on each host
  try:
    is_init, vessels = nm_remote_api.initialize(host_list, "autograder")
  except Exception,e:
    clean_up()
    my_print(str(e))
    raise
  else:
    if not is_init:
      clean_up()
      my_print("Exception, faile dto initialize seattle nodes "+str(vessels))
      raise Exception, 'failed to intialize seattle nodes '+str(vessels)

  
  # get the contents of the students repy file
  student_file_name,student_file_data = data_interface.get_tared_repy_file_data(filename)  

   
  webserver_host_name, webserver_ip = name_ip_tuples[0]
  
  # execute each test in the TEST_DIR
  for (test_name,test_data) in test_tuples:
    
    #reset all vessels before running the test
    nm_remote_api.reset_targets(vessels)
    time.sleep(3)   #give the vessels a little time

    # run the students webserver
    thread.start_new_thread(run_student_code,([vessels[0]],student_file_name,
                             student_file_data))
    time.sleep(3) #give the student code time to start

    testargs =test_name+" "+webserver_ip+" 63173"
    my_print("RUNNING TEST "+test_name+" against "+student_file_name)

    # run the test    
    try:
      test_running,error = nm_remote_api.run_target(vessels[1],test_name,test_data,testargs)
    except Exception,e:
      clean_up()
      my_print(str(e))
      raise
    else:
      if not test_running:
        clean_up()
        my_print("Exception test code: "+test_name+" failed to start: "+error)
        raise Exception, "test code "+test_name+"failed to start\n"+error

    
    # get vessel logs
    try:
      got_it,test_log = nm_remote_api.showlog_vessel(vessels[1])
    except Exception,e:
      clean_up()
      my_print(str(e))
      raise
    else:
      if not got_it:
        clean_up()
        my_print("Exception could not get logs from vessel, error: "+test_log)
        raise Exception, "could not get logs from vessel, error: "+test_log
      

    results = score(test_log,test_name)
    data_interface.save_grade(results,filename)

    
  # mv file to the graded directory
  data_interface.mark_as_graded(filename)

 

  # clean up 
  my_print("tearing down")
  nm_remote_api.tear_down()
 


# call the grade function from the given test
def score(test_log,test_name):
  try:
    repyhelper.translate_and_import(TEST_DIR+"/"+test_name)
    results = grade(test_log)
    return test_name+": "+results
  except Exception:
    my_print("error occured importing grade from "+test_name)
    clean_up()
    raise



## EMULAB REALTED FUNCTIONS

 
# start an expirament in emulab
# blocks for some time waiting for the expirament to go active
def start_emulab():  
  ns_file_name,ns_file_str = data_interface.get_ns_str()

  my_print(" parseing ns file")
  # check the ns file for errors
  (passed,message) = remote_emulab.checkNS(ns_file_str)

  if (not passed):
    my_print(message+"\nException: Failed attempt to parse "+ns_file_name)
    raise Exception, 'Parse of NS file failed'
  
  # start a new exp in non-batchmode
  remote_emulab.startexp(SEATTLE,ASSIGNMENT_NAME,ns_file_str)

  # wait for the exp to go active
  my_print("waiting for exp to go active")
  remote_emulab.wait_for_active(SEATTLE,ASSIGNMENT_NAME,900)

  # get a mapping of host names to internal ips
  emulab_network_mapping = remote_emulab.get_links(SEATTLE,ASSIGNMENT_NAME)
  host_ip_tuples = remote_emulab.simplify_links(SEATTLE,ASSIGNMENT_NAME
                                                 ,emulab_network_mapping)
  my_print('assignment running on emulab')

  return host_ip_tuples





## MAIN LOOP AND CLEAN UP


#terminate the expirament in emulab
def clean_up():
  #try:
  #  remote_emulab.endexp(SEATTLE,ASSIGNMENT_NAME)
  #except Exception,e:
  #  my_print("Exception occured terminating expirament: "+str(e))
  #  raise
  return


# run a loop waiting for files to grade
def waitforfiles():
  while True:

    if data_interface.files_need_grading():

      my_print('starting emulab')
      name_ip_tuples = start_emulab()
      grade_it(name_ip_tuples)
      
      # terminate the expirament
      clean_up()

      
    #sleep for 10 seconds before looping again
    time.sleep(10)    

def fakewaitforfiles():
  while True:
    
    nm_remote_api.tear_down()
    links = [('node-1.'+ASSIGNMENT_NAME+'.Seattle.emulab.net','10.1.1.1'),('node-2.'+ASSIGNMENT_NAME+'.Seattle.emulab.net','10.1.1.2')]
    grade_it(links)



# prints to a log or to the console depending on 
# the golbal make_log
def my_print(data):
  if make_log:
    log.write(str(datetime.datetime.today())+": "+data+"\n")
  else:
    print data


if __name__ == "__main__":

  if len(sys.argv) > 1:  
    if "-p" in argv:
      make_log = False
      print "logging turned off, printing output to console"

  # normal means of running, with emulab part
  #fakewaitforfiles()
  waitforfiles()
 
