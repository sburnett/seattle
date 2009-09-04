"""
<Program Name>
  data_interface.py 

<Started>
  August 2009

<Author>
  Jenn Hanson

<Purpose>
  Provides an abstraction layer between autograder logic and the autograder
  data management levels.  Does not work outside of autograder.

"""
import os
import shutil
import tarfile
import sqlite3


#file paths to the various data components

#directory containing all the student submission tar files
SUBMISSIONS_DIR = '/Users/jenn/Desktop/autograder/submissions/'

#directory containing all the projects
PROJECT_DIR = '/Users/jenn/Desktop/built/meta_test/'

#database containing autograder information (eg student test scores and results)
DATABASE = '/Users/jenn/Desktop/autograder/autograderdatabase.db'






#### private helper methods

def get_list_of_files_in_dir(pathname_to_dir, file_extension_type, error_msg):
  """
  <Purpose>
        Makes a list of all the files in a specified directory with a specified extension type

  <Arguments>
        pathname_to_dir = full pathname to the desired directory
        file_extension_type = string with the extension type (eg if it's '.ns' only ns files will be listed)
        error_msg = string that provides a detailed error message to be used if the directory doesn't exist

  <Exceptions>
        Raises an exception if the directory doesn't exist

  <Side Effects>
        None.

  <Returns>
        List of filenames with the specified file extension found in the directory

  """

  # check if directory exists
  if os.path.isdir(pathname_to_dir) :

    #list of file names to return
    list_of_filenames_in_dir = []

    #get all filenames from directory
    directory_contents = os.listdir(pathname_to_dir)

    #go through list of files in the directory and pick out the ones with the desired extension
    for file_name in directory_contents:
      
      if file_name.endswith(file_extension_type) :
        list_of_filenames_in_dir.append(file_name)

    return list_of_filenames_in_dir

  else :
    raise Exception(error_msg)




  

def get_file_contents(pathname_to_dir, filename, dir_error, file_error):
  """
  <Purpose>
        Reads a desired file and returns its contents

  <Arguments>
        pathname_to_dir = full pathname to the desired directory where the file should exist
        filename = name of the file you want read
        dir_error = error message to report if the directory isn't found
        file_error = error message to report if the file isn't in the specified directory

  <Exceptions>
        Raises an exception if the directory doesn't exist, or the file
        doesn't exist, or there are errors opening/reading the file

  <Side Effects>
        None.

  <Returns>
        Contents of the file

  """

  # check if the directory exists
  if !os.path.isdir(pathname_to_dir) :
    raise Exception(dir_error)
  

  # check if the file exists
  if !os.path.isfile(pathname_to_dir+'/'+filename) :
    raise Exception(file_error)

  # get the contents
  try:
    
    file_obj = open(pathname_to_dir+'/'+filename)
    file_contents = file_obj.read()
    file_obj.close()
    return file_contents
  
  except Exception, e:
    raise



  

def update_something_in_db(query_string, error_msg):
  """
  <Purpose>
        Updates the database

  <Arguments>
        query_string = string containing a database command
        error_msg = string that provides a detailed error message to be used if nothing in the database updates

  <Exceptions>
        Raises an exception if there was a problem opening a
        connection to the database, getting an interactive cursor,
        executing the query, or failing to update anything.

  <Side Effects>
        Updates the database.

  <Returns>
        Nothing.

  """
  conn = None
  cursor = None
  try:
    # Create a connection to the database.
    conn = sqlite3.connect(DATABASE)
    # Create a cursor object to do the interacting.
    cursor = conn.cursor()

    cursor.execute(query_string)
    conn.commit()
    
    if cursor.rowcount < 0 :
      raise Exception(error_msg)

  except Exception, e:
    raise
  
  finally:
    if cursor:
      cursor.close()
    if conn:
      conn.close()




  
def get_query_result_from_db(query_string):
  """
  <Purpose>
        Queries the database and returns the result

  <Arguments>
        query_string = string containing a database query

  <Exceptions>
        Raises an exception if there was a problem opening a
        connection to the database, getting an interactive cursor,
        or executing the query.

  <Side Effects>
        None.

  <Returns>
        Returns the query results which are a list of strings/other variable
        types depending on the desired info from the query string.

        If there were no matching objects in the database, then an empty list will be
        returned.

  """
  #connection to the database
  conn = None
  #cursor object to interact with the database.
  cursor = None
  
  try:
    
    # Create a connection to the database
    conn = sqlite3.connect(DATABASE)
    
    # Create a cursor object to do the interacting.
    cursor = conn.cursor()
    
    # Query the database for a student submission with matching id
    cursor.execute(query_string)
    db_query_results = cursor.fetchall()

    return db_query_results

  except Exception, e:
    e.args = "Error in operations with the database.Specifically:\n%s" % e.args
    raise
  
  finally:
    # Close connections to the database
    if cursor:
      cursor.close()
    if conn:
      conn.close()
    




######public methods
def get_submissions_to_grade(project_id):
    """
  <Purpose>
        Gets a list of student submission id's for submissions that are ready to be
        graded for assignments based of the project with project_id

  <Arguments>
        project_id = an integer that is the primary id for the project_description class in the database

  <Exceptions>
        Raises Exception if thereare problems accessing or querying the database with the specified project_id

  <Side Effects>
        None.

  <Returns>
        list of student submission id's

  """

  #list of student submission unique id's for submissions that need to be graded
  list_of_submission_ids = []

  #make sql query that finds all student submissions waiting to be graded that are for assignments created from the project with unique id project_id
  query_string = 'SELECT course_student_submission.id from course_student_submission, course_assignment'
  query_string = query_string +' WHERE course_assignment.project_id = '+str(project_id)+' AND course_student_submission.assignment_id = '
  query_string = query_string + 'course_assignment.id AND course_student_submission.grade_results = "waiting to be graded"'

  #run the query
  try:
    
    query_results = get_query_result_from_db(query_string)
    
  except Exception, e:
    raise
  
  #loop through results to append to list appropriately
  for result in query_results:
    
    list_of_submission_ids.append(result[0])
  
  #return list
  return list_of_submission_ids



  
  
#methods that deal with changing/saving results/scores status
def get_results(submission_id):

  """
  <Purpose>
        Gets the string results stored for the specific student submission

  <Arguments>
        submission_id = an integer that is the primary id for the student_submission in the database

  <Exceptions>
        Raises Exception if there is no student submission for the submission_id

  <Side Effects>
        None.

  <Returns>
        String that gives the results of grading the associated student submission.
        This string will either say that it hasn't been graded, grading is in progress, or give detailed results of the grading

  """
  try:
    
    #make query string 
    query_string = 'SELECT results FROM course_student_submission WHERE id='+str(submission_id)
    #get query results
    query_results = get_query_result_from_db()
    
  except Exception, e:
    raise
      
  #Check that a submission was found or raise an error
  if len(query_results) == 0:
    error_msg = 'No submission found with the id: '+ str(submission_id)
    raise Exception(error_msg)

  else:
    return db_query_results[0][0]






def get_score(submission_id):

  """
  <Purpose>
        Gets the integer score stored for the specific student submission

  <Arguments>
        submission_id = an integer that is the primary id for the student_submission in the database

  <Exceptions>
	Raises Exception if there is no student submission for the submission_id

  <Side Effects>
        None.

  <Returns>
        An integer representing the student's score from grading the submission.  If the submission hasn't been graded yet, 0 is returned.

  """
  try:
    
    #make query string 
    query_string = 'SELECT score FROM course_student_submission WHERE id='+str(submission_id)
    #get query results
    query_results = get_query_result_from_db()
    
  except Exception, e:
    raise
      
  #Check that a submission was found or raise an error
  if len(query_results) == 0:
    error_msg = 'No submission found with the id: '+ str(submission_id)
    raise Exception(error_msg)

  else:
    return db_query_results[0][0]





def change_results(submission_id, new_results):

  """
  <Purpose>
	Updates the saved results for the student submission

  <Arguments>

        submission_id = an integer that is the primary id for the student_submission in the database

        new_results = string that gives the new grading results for the submission

  <Exceptions>
	Raises Exception if there is no student submission for the submission_id or if new_results is not a string

  <Side Effects>
        Updates the grade results stored for the particular student submission.

  <Returns>
        Nothing.

  """
  try:
    
    #make sql command string to update the results
    query_string = 'UPDATE course_student_submission SET results='+str(new_results)+' WHERE id='+ str(submission_id)

    #make error message
    error_msg = 'The results could not be updated for the submission with id '+str(submission_id)

    #execute the command
    update_something_in_db(query_string, error_msg)

  except Exception, e:
    raise

  




def change_score(submission_id, new_score):

  """
 <Purpose>
	Updates the score for the student submission

  <Arguments>

        submission_id = an integer that is the primary id for the student_submission in the database

        new_score = integer that represents the student's new score for this submission

  <Exceptions>
	Raises Exception if there is no student submission for the submission_id or if new_score is not an integer


  <Side Effects>
        Updates the score for the corresponding submission.

  <Returns>
        Nothing.

  """
  try:
    
    #make sql command string to update the results
    query_string = 'UPDATE course_student_submission SET score='+str(new_results)+' WHERE id='+ str(submission_id)

    #make error message
    error_msg = 'The score could not be updated for the submission with id '+str(submission_id)

    #execute the command
    update_something_in_db(query_string, error_msg)

  except Exception, e:
    raise




#methods that deal with getting ns file stuff

def get_ns_file_list(assignment_id):

  """
  <Purpose>

	Gets the list of ns file names corresponding to this assignment.

  <Arguments>

	assignment_id = unique id for the assignment

  <Exceptions>

	Raises an Exception if there is no assignment for the assignment_id

  <Side Effects>

        None.

  <Returns>

	List of strings of the ns file names for the assignment

  """

  # make full pathname to test suite directory for the specified assignment
  ns_pathname = PROJECT_DIR + str(assignment_id) +'/ns_files'
  
  #only want ns files
  file_extension_type = '.ns'
  
  #make error message
  error_msg = 'There is no directory of ns files for the assignment with id: '+str(assignment_id)

  try:
  
    get_list_of_files_in_dir(ns_pathname, file_extension_type, error_msg)
    
  except Exception, e:
    raise
  



def get_ns_contents(assignment_id, ns_file_name):

  """
  <Purpose>

	Gets the contents of a specific ns file 

  <Arguments>

	assignment_id = unique id for the assignment

	ns_file_name = name of the ns file from which you want the contents

  <Exceptions>

	Raises an Exception if their is no assignment matching assignment_id or if there is no ns file with ns_file_name for the assignment

  <Side Effects>

	None.

  <Returns>

	Returns the contents of the specified ns file

  """
  # make full pathname to ns file suite directory for the specified assignment
  ns_pathname = PROJECT_DIR + str(assignment_id)+'/ns_files'
  
  #make error message if the file isn't in the directory
  file_error = 'There is no ns file with the name  "'+ns_file_name+'" for the assignment with id '+str(assignment_id)
  
  #make error message if the directory doesn't exist
  dir_error = 'There is no ns file directory for the assignment with id: '+str(assignment_id)
  
  try:
    return get_file_contents(ns_pathname, ns_file_name, dir_error, file_error)
  except Exception, e:
    raise

                      



#methods that deal with getting test suite stuff

def get_test_list(assignment_id):
  """
  <Purpose>

	Gets the list of test files in the test suite for this assignment

  <Arguments>

        assignment_id = unique id for the assignment

  <Exceptions>

	Raises an Exception if there is no assignment with the assignment_id

  <Side Effects>

	None.

  <Returns>

	Returns a list of strings of the file names of the tests for the specified assignment.

  """
  # make full pathname to test suite directory for the specified assignment
  test_suite_pathname = PROJECT_DIR + str(assignment_id) +'/test_suite'
                      
  #only want repy files
  file_extension_type = '.repy
                      
  #make error message if the directory can't be found
  error_msg = 'There is no test suite for the assignment with id: '+str(assignment_id)
  
  try:
                      
    get_list_of_files_in_dir(test_suite_pathname, file_extension_type, error_msg)

  except Exception, e:
    raise





def get_test_contents(assignment_id, test_file_name):

  """

  <Purpose>

	Gets the contents of a test file 

  <Arguments>

        assignment_id = unique id for the assignment

        test_file_name = name of the test file from which you want the contents

  <Exceptions>

        Raises an Exception if their is no assignment matching assignment_id or if there is no test file with test_file_name for the assignment

  <Side Effects>

        None.

  <Returns>

        Returns the contents of the specified test file

  """

  # make full pathname to test suite directory for the specified assignment
  test_suite_pathname = PROJECT_DIR + str(assignment_id) +'/test_suite'
  
  #make error message if the file isn't in the directory
  file_error = 'There is no test file with the name  "'+test_file_name+'" for the assignment with id '+str(assignment_id)
  
  #make error message if the directory doesn't exist
  dir_error = 'There is no test suite for the assignment with id: '+str(assignment_id)
  
  try:
    return get_file_contents(test_suite_pathname, test_file_name, dir_error, file_error)
  except Exception, e:
    raise







#methods that deal with getting student submissions stuff
def get_student_files_list(submission_id):

  """
  <Purpose>

	Gets the list of all the file names inside the student's compressed tar file submission

  <Arguments>

        submission_id = an integer that is the primary id for the student's submission

  <Exceptions>

        Raises an Exception if there is no student submission for the submission_id.

  <Side Effects>

        None.

  <Returns>

        Returns a list of strings of the file names in the specified student submission tar file.

  """

  # Query the database for a student submission with matching id
  query_string = 'SELECT student_code_filename FROM course_student_submission WHERE id=' + str(submission_id)

  try:
    query_results = get_query_result_from_db(query_string)
    
    #Check that a submission was found or raise an error
    if len(query_results) == 0 :
      error_msg = 'No submission found with the id: '+ str(submission_id)
      raise Exception(error_msg)

    else:
      # make full file path to tarred file
      submission_filename = SUBMISSIONS_DIR + query_results[0][0]

      # get tarred file
      tar = tarfile.open(submission_filename)
  
      # get the list of files in the tar
      file_name_list = tar.getnames()
      tar.close()
      return file_name_list
    
  except Exception, e:
    raise





def get_submission_contents(submission_id, student_code_filename):

  """
  <Purpose>

	Gets the contents of a specific file in the student submission's compressed tar file.

  <Arguments>

        submission_id = an integer that is the primary id for the student_submission in the database

        student_code_filename = file name from the student's submitted tar file which you want the contents

  <Exceptions>

        Raises an Exception if their is no submission matching submission_id or if there is no file with file_name in the submission compressed tar file

  <Side Effects>

        Nothing.

  <Returns>

        Returns the contents of the specified file

  """

  #make sql query string for database
  query_string = 'SELECT student_code_filename FROM course_student_submission WHERE id='+str(submission_id)

  try:
    
    # Query the database for a student submission with matching id
    query_results = get_query_result_from_db(query_string)
    
    #Check that a submission was found or raise an error
    if len(query_results) == 0 :
      error_msg = 'No submission found with the id: '+ str(submission_id)
      raise Exception(error_msg)

    else:
      # make full file path to tarred file
      submission_filename = SUBMISSIONS_DIR + query_results[0][0]

      # get tarred file
      tar = tarfile.open(submission_filename)

      # cycle through names of files in the tar to see if any match 
      file_names_in_tar = tar.getnames()

      for name_from_tarlist in file_names_in_tar:
        
        if name_from_tarlist == student_code_filename:
          
          file_obj = tar.extractfile(name)
          file_contents = file_obj.read()
          file_obj.close()
          tar.close()
          
          return file_contents

      raise Exception( student_code_filename+' not found in the student submission with id '+str(submission_id))
    
  except Exception, e:
    raise
