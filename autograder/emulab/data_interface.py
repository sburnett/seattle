"""
<Program Name>
  data_interface.py 

<Started>
  3/01/2009

<Author>
  Eric Kimbrel, kimbrl@cs.washington.edu

<Purpose>
  Provides an abstraction layer between autograder logic and the autograder
  data management levels.  Is not inteded to be used outside of 
  autograder_runner.py.

"""




import os
import shutil
import tarfile

#TO_GRADE_DIR = '/tmp/sal/ToGrade'
TO_GRADE_DIR = 'to_grade'

#GRADED_DIR = '/tmp/sal/Graded'
GRADED_DIR = 'graded'

#STATUS_DIR = '/tmp/sal/Status'
STATUS_DIR = 'status'

TEST_DIR = 'meta_test'



#####TEMPORARY TEST_META_DATA DICT CREATION
# This is a hard coded dictionary to facilitate the grading of the
# webserver assignment.  It will be replaced in the future with generic methods
# that pull assignemnt data from a data base

# return a tuple of test meta data
def get_test_meta_data(assignment_name):
  
  list_of_tests = get_test_names()

  nsfile_list = ['wlan.ns']  
  nsfile_testsuite_map = {'wlan.ns':list_of_tests}      # map ns files to test_suites (list of tests)
  
  test_node_map = {}     #{testname:[{dict contatinging info for a test node}....]

  
  # the expirament name in emulab will be the assignment name + the nsfile name (without .ns at the end)
  node1 = 'node-1.'+assignment_name+'wlan.Seattle.emulab.net'
  node2 = 'node-2.'+assignment_name+'wlan.Seattle.emulab.net'

  # set node1 to student code and node 2 to test for all test
  # make a test_node_map entry for each test
  for test_name in list_of_tests:
    
    # ORDER MATTERS!  the order of the list is the order of execution
    test_node_map[test_name] = [{'node':node1,'code':'webserver.repy','get_logs':False,'block':False,'is_student':True,
                                             'args':'63173'},
                                       {'node':node2,'code':test_name,'get_logs':True,'block':True,'is_student':False,
                                             'args':'10.1.1.1 63173'}]
                                    
  return (nsfile_list,nsfile_testsuite_map,test_node_map)


#returns a list of test names from the TEST_DIR
def get_test_names():
  names=[]
  dir_contents = os.listdir(TEST_DIR)
  for test in dir_contents:
    if test[-4:] == 'repy':
      names.append(test)

  return names

####END TEMPORARY META_DATA CREATION


# The following methods currently act on files and directories
# they should be replaced by database methods.
# This will likely cause the method signatures to change so the
# corresponding logic in autograder_runner.py will need to change as well


# write 'grading in progress' at the top of a file
def mark_in_progress(filename):
  # update status folder to grading in progress
  file_obj = open(STATUS_DIR+"/"+filename+".txt",'r+')
  file_obj.write("Grading in progress")
  file_obj.close()
  


# return the contents of the ns_file specified
# it is assumed that the ns file will be located
# in the test directory
def get_ns_str(ns_file_name):
  ns_file_obj = open(TEST_DIR+"/"+ns_file_name)
  ns_file_str = ns_file_obj.read()
  ns_file_obj.close()
  return ns_file_str
  


# determine if there are files ready to grade
def files_need_grading():
  return len(os.listdir(TO_GRADE_DIR)) > 0

# get a list of files that need to be graded
def files_to_grade():
  return os.listdir(TO_GRADE_DIR)



# returns the contents of .repy file that is compressed in a tar file
# assumes the file in question is in the TO_GRADE directory
def get_tared_repy_file_data(tarname,filename):
  tar = tarfile.open(TO_GRADE_DIR+"/"+tarname)
  names = tar.getnames()
  for name in names:
    if name == filename:  
      file_obj = tar.extractfile(names[0])
      data = file_obj.read()
      file_obj.close()
      tar.close()
      return names[0], data
  raise Exception, filename+' not found in '+tarname



# move file to the graded folder
def mark_as_graded(filename):
 shutil.move(TO_GRADE_DIR+"/"+filename, GRADED_DIR+"/"+filename)


# returns the contents of a file located in the TEST_DIR
def get_test_content(filename):
  file_obj = open(TEST_DIR+"/"+filename)
  data = file_obj.read()
  file_obj.close()
  return data
    




# TODO Grading Complete is marked after the first test completes
# It shouldn't be marked complete until all tests have ran
# save the result of grading to the status dir
# assumes this file allready exisits in the directory
def save_grade(results,filename):
  
  # check to see if grading status is complete
  file_obj = open(STATUS_DIR+"/"+filename+".txt",'r')
  contents = file_obj.read()
  file_obj.close()
  if contents.find("Grading Complete") == -1:
    file_obj = open(STATUS_DIR+"/"+filename+".txt",'w')  
    file_obj.write("Grading Complete\n<br>")
  else:
    file_obj = open(STATUS_DIR+"/"+filename+".txt",'a')
  
  file_obj.write(results+"<br>")
  file_obj.close()




# append both the result of the grade function and
# the test logs to the status_file
def save_output(filename,test_name,results,test_log):
  
  mark_in_progress = False

  #is grading already in progress
  file_obj = open(STATUS_DIR+"/"+filename+".txt")
  progress_str = file_obj.readline()
  if "grading in progress" not in progress_str:
    mark_in_progress = True
    file_obj.close()
    os.remove(STATUS_DIR+"/"+filename+".txt")  # just remove the file since it has nothing
  else: file_obj.close()

  #save the results of grading to the status file
  file_obj = open(STATUS_DIR+"/"+filename+".txt",'a')
  if mark_in_progress: file_obj.write("grading in progress...\n")
  file_obj.write(results+'\n')
  file_obj.close()

  #save the full test output to a temporary file
  file_obj = open(STATUS_DIR+"/"+filename+"TEMP.txt",'a')
  file_obj.write(test_name+' details: \n'+test_log+'\n')
  file_obj.close()


# combine the grade results with the test logs
def concat_status_files(student_file):
 
  file_obj_temp =  open(STATUS_DIR+"/"+student_file+"TEMP.txt")
  details = file_obj_temp.read()
  file_obj_temp.close()
  os.remove(STATUS_DIR+"/"+student_file+"TEMP.txt")

  file_obj_status = open(STATUS_DIR+"/"+student_file+".txt")
  status_str = file_obj_status.read()
  file_obj_status.close()

  #replace grading in progress with grading complete
  status_str.replace("grading in progress","Grading Complete",1)

  file_obj_final = open(STATUS_DIR+"/"+student_file+".txt",'w')
  file_obj_final.write("Grading Completed \n"+status_str)
  file_obj_final.write("\nFULL DETAILS\n"+details)
  file_obj_final.close()

  
