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


  # Create a connection to the database
  conn = sqlite3.connect(DATABASE)


  # Create a cursor object to do the interacting.
  cursor = conn.cursor()


  # Query the database for a student submission with matching id
  cursor.execute('SELECT results FROM course_student_submission WHERE id=?',submission_id)
  db_query_results = cursor.fetchone()


  # Close connections to the database
  cursor.close()
  conn.close()


  #Check that a submission was found or raise an error
  if db_query_results == None :
    error_msg = 'No submission found with the id: '+ str(submission_id)
    raise Exception(error_msg)

  else:
    return db_query_results[0]






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


  # Create a connection to the database
  conn = sqlite3.connect(DATABASE)


  # Create a cursor object to do the interacting.
  cursor = conn.cursor()


  # Query the database for a student submission with matching id
  cursor.execute('SELECT score FROM course_student_submission WHERE id=?',submission_id)
  db_query_results = cursor.fetchone()


  # Close connections to the database
  cursor.close()
  conn.close()


  #Check that a submission was found or raise an error
  if db_query_results == None :
    error_msg = 'No submission found with the id: '+ str(submission_id)
    raise Exception(error_msg)

  else:
    return db_query_results[0]





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


  # Create a connection to the database.
  conn = sqlite3.connect(DATABASE)


  # Create a cursor object to do the interacting.
  cursor = conn.cursor()


  # query the database to make sure there is a student submission matching the id
  cursor.execute('SELECT * FROM course_student_submission WHERE id=?', (submission_id,))
  old_result = cursor.fetchone()


  #Check that a submission was found or raise an error
  if db_query_results == None :

    cursor.close()
    conn.close()

    error_msg = 'No submission found with the id: '+ str(submission_id)
    raise Exception(error_msg)

  else:

    cursor.execute('UPDATE course_student_submission SET results=? WHERE id=?', (new_results, submission_id))
   
    # Commit the changes and close everything.
    conn.commit()
    cursor.close()
    conn.close()





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


  # Create a connection to the database.
  conn = sqlite3.connect(DATABASE)

  # Create a cursor object to do the interacting.
  cursor = conn.cursor()


  # query the database to make sure there is a student submission matching the id
  cursor.execute('SELECT * FROM course_student_submission WHERE id=?', (submission_id,))
  old_result = cursor.fetchone()


  #Check that a submission was found or raise an error
  if db_query_results == None :
    cursor.close()
    conn.close()

    error_msg = 'No submission found with the id: '+ str(submission_id)
    raise Exception(error_msg)

  else:
    cursor.execute('UPDATE course_student_submission SET score=? WHERE id=?', (new_score, submission_id))

   

    # Commit the changes and close everything.
    conn.commit()
    cursor.close()
    conn.close()






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


  # check if it exists
  if os.path.isdir(ns_pathname) :

    ns_file_list = []
    directory_contents = os.listdir(ns_pathname)

    for file_name in directory_contents:
      if file_name.endswith('.ns') :
        ns_file_names.append(file_name)

    return ns_file_names

  else :
    raise Exception('There is no directory of ns files for the assignment with id: '+str(assignment_id))






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


  # make full pathname to test suite directory for the specified assignment
  ns_pathname = PROJECT_DIR + str(assignment_id)+'/ns_files'


  # check if it exists
  if os.path.isdir(ns_pathname) :

    # make pathname to specified file in the test suite directory
    ns_file_pathname = ns_pathname + '/' + ns_file_name


    # check if the file exists
    if os.path.isfile(ns_file_pathname) :

      # get the contents
      file_obj = open(ns_file_pathname)
      file_contents = file_obj.read()
      file_obj.close()
      return file_contents

    else :

      raise Exception('There is no ns file with the name  "'+ns_file_name+'" for the assignment with id '+str(assignment_id)

  else :

    raise Exception('There is no ns file directory for the assignment with id: '+str(assignment_id))





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


  # check if it exists
  if os.path.isdir(test_suite_pathname) :

    test_names_list = []
    directory_contents = os.listdir(test_suite_pathname)

    for test_name in directory_contents:
      if test_name.endswith('.repy') :
        test_names.append(test_name)

    return test_names

  else :

    raise Exception('There is no test suite for the assignment with id: '+str(assignment_id))





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


  # check if it exists
  if os.path.isdir(test_suite_pathname) :

    # make pathname to specified file in the test suite directory
    test_file_pathname = test_suite_pathname + '/' + test_file_name


    # check if the file exists
    if os.path.isfile(test_file_pathname) :


      # get the contents
      file_obj = open(test_file_pathname)
      file_contents = file_obj.read()
      file_obj.close()
      return file_contents

    else :

      raise Exception('There is no test file with the name  "'+test_file_name+'" for the assignment with id '+str(assignment_id)

  else :
    raise Exception('There is no test suite for the assignment with id: '+str(assignment_id))







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


  # Create a connection to the database
  conn = sqlite3.connect(DATABASE)


  # Create a cursor object to do the interacting.
  cursor = conn.cursor()


  # Query the database for a student submission with matching id
  cursor.execute('SELECT student_code_filename FROM course_student_submission WHERE id=?', submission_id)
  db_query_results = cursor.fetchone()

  # Close connections to the database
  cursor.close()
  conn.close()

  #Check that a submission was found or raise an error
  if db_query_results == None :
    error_msg = 'No submission found with the id: '+ str(submission_id)
    raise Exception(error_msg)

  else:
    # make full file path to tarred file
    submission_filename = SUBMISSIONS_DIR + db_query_results[0]

    # get tarred file
    tar = tarfile.open(submission_filename)
  

    # get the list of files in the tar
    file_name_list = tar.getnames()
    tar.close()
    return file_name_list





def get_submission_contents(submission_id, file_name):

  """

  <Purpose>


Gets the contents of a specific file in the student submission's compressed tar file.


  <Arguments>


        submission_id = an integer that is the primary id for the student_submission in the database


        file_name = file name from which you want the contents


  <Exceptions>


        Raises an Exception if their is no submission matching submission_id or if there is no file with file_name in the submission compressed tar file


  <Side Effects>


        Nothing.


  <Returns>


        Returns the contents of the specified file


  """

 # Create a connection to the database
  conn = sqlite3.connect(DATABASE)

  # Create a cursor object to do the interacting.
  cursor = conn.cursor()


  # Query the database for a student submission with matching id
  cursor.execute('SELECT student_code_filename FROM course_student_submission WHERE id=?', submission_id)
  db_query_results = cursor.fetchone()


  # Close connections to the database
  cursor.close()
  conn.close()


  #Check that a submission was found or raise an error
  if db_query_results == None :
    error_msg = 'No submission found with the id: '+ str(submission_id)
    raise Exception(error_msg)

  else:
    # make full file path to tarred file
    submission_filename = SUBMISSIONS_DIR + db_query_results[0]


    # get tarred file
    tar = tarfile.open(submission_filename)

  

    # cycle through names of files in the tar to see if any match 
    file_names = tar.getnames()

    for name in file_names:
      if name == file_name:  
        file_obj = tar.extractfile(name)
        file_contents = file_obj.read()
        file_obj.close()
        tar.close()
        return file_contents

    raise Exception( filename+' not found in the student submission with id '+submission_id)
