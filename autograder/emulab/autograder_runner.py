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


#TODO
#and try excepts
# check status of running targets
# get alpers reset
# integrate with jenn




import os
import shutil
import remote_emulab
import install_autograder
import repyhelper
import threading

TO_GRADE_DIR = 'to_grade'
GRADED_DIR = 'graded'
STATUS_DIR = 'status'
TEST_DIR = 'temp_test'
SEATTLE = 'Seattle'  # the name of our project in emulab
ASSIGNMENT_NAME = 'webserver' #emulab exp name





## FUNCTIONS TO RUN AND GRADE REPY CODE 


# use a thread to run student code, blocks
# until the code is done executing
class Student_code_runner(threading.Thread):
  def __init__(self,vessel,student_file_name,student_file_data):
    self.vessel=vessel
    self.student_file_name = student_file_name 
    self.student_file_data = student_file_data
  
  def run(self):
    

    print "\n"+self.vessel+"\n"+self.student_file_name
    print self.student_file_data

    try:
      webserver_running,error = install_autograder.run_target(self.vessel,
                            self.student_file_name,self.student_file_data,
                            self.student_file_name+' 63173')
    except Exception:
      clean_up()
      raise
    else:
      if not webserver_running:
        clean_up()
        raise Exception, "student code failed to start: "+error
   
  def stop(self):
    install_autograder.stop_target(self.vessel)
    #TODO CLEAR LOGS


# coordinate running code on emulab and processing the output
def grade(name_ip_tuples):
  
  print "Starting grading"

  while files_need_grading():

    file_to_grade = next_file_to_grade()

    # update status folder to grading in progress
    file_obj = open(STATUS_DIR+"/"+file_to_grade+".txt",'r+')
    file_obj.write("Grading in progress")
    file_obj.close()
  
    # execute the assignment and tests in emulab
    run_webserver_tests(file_to_grade,name_ip_tuples)


# execute repy code on emulab nodes
def run_webserver_tests(filename,name_ip_tuples): 

  # get a tuple for each test [(filename,file_content_str)...]
  test_tuples = get_tests()

  # get the student file to grade
  file_obj = open(TO_GRADE_DIR+"/"+filename,'r')
  student_file_data = file_obj.read()
  file_obj.close()

  #get list of hosts
  host_list =[]
  for (host,ip) in name_ip_tuples:
    host_list.append(host)

  print "initializing vessels"
  
  # initialize seattle nodes on each host
  try:
    is_init, vessels = install_autograder.initialize(host_list, "autograder")
  except Exception:
    clean_up()
    raise
  else:
    if not is_init:
      raise Exception, 'failed to intialize seattle nodes '+str(vessels)

  #create a thread to run student code
  student_code_thread = Student_code_runner(vessels[0],
                             filename,student_file_data)


  #TODO, reset all nodes after each test  
  webserver_host_name, webserver_ip = name_ip_tuples[0]
  for (test_name,test_data) in test_tuples:
    
    # run the students webserver
    student_code_thread.run()

    testargs =test_name+" "+webserver_ip+"63173"
    print "running test "+test_name+" against "+filename
    
    # run the test    
    try:
      test_running,error = install_autograder.run_target(vessels[1],
                             test_name,test_data,testargs)
    except Exception:
      clean_up()
      raise
    else:
      if not test_running:
        clean_up()
        raise Exception, "test code "+test_name+"failed to start\n"+error

    
    # get vessel logs
    try:
      #server_log =  install_autograder.showlog_vessel(vessels[0])
      test_log = install_autograder.showlog_vessel(vessels[1])
    except Exception:
      clean_up()
      raise
    
    # stop the repy code
    install_autograder.stop_target(vessel[1])
    student_code_thread.stop()

    results = score(test_log,test_name)
    save_grade(results,filename)

    #reset the nodes
    

  # mv file to the graded directory
  shutil.move(TO_GRADE_DIR+"/"+filename, GRADED_DIR+"/"+filename)

  # clean up 
  install_autograder.tear_down()
  for test_name,test_obj in test_tuples:
    test_obj.close()



# call the grade function from the given test
def score(test_log,test_name):
  try:
    repyhelper.translate_and_import(TEST_DIR+"/"+test_name)
    results = grade(test_log)
    return results
  except Exception:
    print "error occured importing grade from "+test_name
    clean_up()
    raise



## EMULAB REALTED FUNCTIONS

 
# start an expirament in emulab
# blocks for some time waiting for the expirament to go active
def start_emulab():  
  ns_file_name,ns_file_str = get_ns_str()

  print " parseing ns file"
  # check the ns file for errors
  (passed,message) = remote_emulab.checkNS(ns_file_str)

  if (not passed):
    print message
    print "Failed attempt to parse "+ns_file_name
    print "Expirament could not be started"
    raise Exception, 'Parse of NS file failed'
  
  # start a new exp in non-batchmode
  remote_emulab.startexp(SEATTLE,ASSIGNMENT_NAME,ns_file_str)

  # wait for the exp to go active
  print "waiting for exp to go active"
  remote_emulab.wait_for_active(SEATTLE,ASSIGNMENT_NAME,900)

  # get a mapping of host names to internal ips
  emualb_network_mapping = remote_emulab.get_links(SEATTLE,ASSIGNMENT_NAME)
  host_ip_tuples = remote_emulab.simplify_links(SEATTLE,ASSIGNMENT_NAME
                                                 ,emulab_network_mapping)
  print 'assignment running on emulab'

  return host_ip_tuples



## FILE AND DIRECTORY RELATED FUNCTIONS


# get the ns file string from the first ns file in the TEST_DIR
# returns the name of the ns file, and a string representing the file
# if an ns file is not found throw an exception
def get_ns_str():
  ns_file = None
  ns_file_str = None
  test_files = os.listdir(TEST_DIR)
  
  #use the first ns file found
  for file_name in test_files:
    if file_name[-2:] == 'ns':
      ns_file = file_name
      break
  
  if ns_file is not None:
    ns_file_obj = open(TEST_DIR+"/"+ns_file)
    ns_file_str = ns_file_obj.read()
    ns_file_obj.close()
    return ns_file,ns_file_str
  else:
    raise Exception, 'Failed to get the NS File'


# determine if there are files ready to grade
def files_need_grading():
  return len(os.listdir(TO_GRADE_DIR)) > 0

# get a list of files that need to be graded
def files_to_grade():
  return os.listdir(TO_GRADE_DIR)

#reutrn the name of the next file to grade
def next_file_to_grade():
  file_list = files_to_grade()
  return file_list[0]

# save the result of grading to the status dir
def save_grade(results,filename):
  file_obj = open(STATUS_DIR+"/"+filename+".txt",'a')
  file_obj.write(results)
  file_obj.close()

# return a list of tuples
# (filename,filedata) for each test that needs to be run
def get_tests():
  tuples =[]
  # get the list of tests
  test_list = os.listdir(TEST_DIR)
  for test in test_list:
    if test[-4:] == 'repy':
      file_obj = open(TEST_DIR+"/"+test)
      data = file_obj.read()
      file_obj.close()
      tuples.append((test,data))
  return tuples



## MAIN LOOP AND CLEAN UP


#terminate the expirament in emulab
def clean_up():
  #remote_emulab.endexp(SEATTLE,ASSIGNMENT_NAME)
  return


# run a loop waiting for files to grade
def waitforfiles():
  while True:

    if files_need_grading():

      print 'starting emulab'
      name_ip_tuples = start_emulab()
      grade(name_ip_tuples)
      
      # terminate the expirament
    

    #temporary break so we just do this once for testing  
    print "FINISHED!"
    break  
    

if __name__ == "__main__":

  # normal means of running, with emulab part
  #waitforfiles()
  
  # temp code for running on exisiting emulab exp
  
  install_autograder.tear_down()
  links = [('node-1.webserver.Seattle.emulab.net','10.1.1.1'),('node-2.webserver.Seattle.emulab.net','10.1.1.2')]
  grade(links)
