"""
<Program Name>
  data_interface.py 

<Started>
  3/01/2009

<Author>
  Eric Kimbrel, kimbrl@cs.washington.edu

<Purpose>
  Provides an abstraction layer between autograder logic and the autograder
  data management levels.  Is not inteded to be used outside of the autograder.

"""





## FILE AND DIRECTORY RELATED FUNCTIONS
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



def mark_in_progress(filename):
  # update status folder to grading in progress
  file_obj = open(STATUS_DIR+"/"+filename+".txt",'r+')
  file_obj.write("Grading in progress")
  file_obj.close()
  

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
    my_print("Exception Raised, Failed to get the NS FILE")
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

# returns the contents of .repy file that is compressed in a tar file
def get_tared_repy_file_data(filename):
  
  if filename[-3:] != "tar":
    clean_up()
    my_print("Exception, file to grade was not a tar")
    raise Exception, "file to grade was not a tar file"
  tar = tarfile.open(TO_GRADE_DIR+"/"+filename)
  names = tar.getnames()
  if len(names) != 1:
    tar.close()
    clean_up()
    my_print("Exception Tarfile did not have exactly one thing it in")
    raise Exception, "Tarfile did not have exactly one thing in it"
  if names[0][-4:] != "repy":
    tar.close
    clean_up()
    my_print("Exception Tarfile did not contatin a repy file")
    raise Exception, "Tarfile did not contain a repy file"

  file_obj = tar.extractfile(names[0])
  data = file_obj.read()
  file_obj.close()
  tar.close()
  return names[0], data

# move file to the graded folder
def mark_as_graded(filename):
 shutil.move(TO_GRADE_DIR+"/"+filename, GRADED_DIR+"/"+filename)


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



#TODO Grading Complete is marked after the first test complets
# save the result of grading to the status dir
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


#TODO Grading Complete is marked after the first test complets
# save the result of grading to the status dir
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
