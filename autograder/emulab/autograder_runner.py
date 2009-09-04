"""
<Program Name>
  autograder_runner.py 

<Started>
  August 28, 2009

<Author>
  Jenn Hanson

<Purpose>
  Management script that coordinates testing and grading for all
  student submissions for the autograder.

  It gets a list of current projects via data_interface and spawns
  a thread for each.  Each thread runs a loop looking for new student
  submissions to be graded.  If new submissions are found custom testing
  and grading submissions are called and the resulting score and results
  summary are saved.

"""

import thread
from data_interface import *


#Import all testing and grading python scripts
import webserver.test
import webserver.grade 


#List of projects to run through
#
#Each project in projects list should consist of a 4-tuple:
# (project_name, project_id, test_method, grade_method)
#
# project_name = string name for the project
# project_id = unique primary key in the database for the specified project
# test_method = method name from the test script for the specific project
# grade_method = method name from the grade script for the specific project
projects_list = ()




def populate_project_list():
  """
  <Purpose>
      populates the global list projects_list with info on all current projects

  <Arguments>
      None.
        
  <Exceptions>
      None.
        
  <Side Effects>
      changes projects_list

  <Returns>
      Nothing.

  """
  
  #clear the list
  projects_list = ()
  
  #add each project individually to project_dict...yeah this is really cumbersome and
  #should probably be changed to something better later
  new_project = ('webserver', 1, webserver.test.run_testing, webserver.run_grading)
  projects_list.append(new_project)




#to do: don't currently use project_name but will probably use it when autograder_api is fixed
def run_project(project_name, project_id, test_method, grade_method):
  """
  <Purpose>
      Runs through all the logic behind grading student submissions for a specific project.
      Loops continuously looking for new submissions to grade.

  <Arguments>
        project_name = string name for the project
        project_id = primary key in the database for the project
        test_method = method name that contains all the logic for testing a student submission
        grade_method = method name htat contains all the logic for grading the results from the test_method
        
  <Exceptions>
        None.
        
  <Side Effects>
        updates grade_results and scores for student_submission objects in the database
        prints error messages 

  <Returns>
        Nothing.

  """
  
  global data_lock

  while(True):
    #get a list of student submissions to be graded
    submissions_list = get_submissions_to_grade(project_id)

    
    #loop through the submissions and test/grade them
    for submission_id in submission_list:

      #need to update info in database
      data_lock.acquire()

      try:
        
        #update grade and status to reflect new info
        change_results(submission_id, 'grading in progress')
        change_score(submission_id, 0)
        
      except Exception, e:
        error_msg = 'Error in autograder_runner.run_project while trying to update the grading_status and score for student_submission with id: '+str(submission_id)+'\nError message is: '+str(e)
        print error_msg

        #unlock so other threads can use it
        data_lock.release()
        
      else:

        #unlock so other threads can use it
        data_lock.release()
        
        try:
          
          rough_results = test_method('need args here')
          (new_score, new_results) = grade_method(rough_results)
          
        except Exception, e:
          error_msg = 'Error in autograder_runner.run_project while trying to test/grade student_submission with id: '+str(submission_id)+'\nError message is:  '+str(e)
          print error_msg

          #set grading status back to 'waiting to be graded' so in case it's a temporary problem, the submission can be picked up and graded later
          change_results(submission_id, 'waiting to be graded')
          change_score(submission_id, 0)
          
        else:
          
          #need to update info in database
          data_lock.acquire()
      
          #update grade and status to reflect new info
          change_results(submission_id, new_results)
          change_score(submission_id, new_score)

          #unlock so other threads can use it
          data_lock.release()





def main():
  """
  <Purpose>
      starts the threads for grading submissions for each of the different projects

  <Arguments>
        None.
        
  <Exceptions>
        None.
        
  <Side Effects>
        starts a new thread for each project

  <Returns>
        Nothing

  """
  
  #run through the list of assignments and start a thread for grading each one
  for (proj_name, proj_id, test_method, grade_method) in project_list:
    
    thread.start_new_thread(run_project,(proj_name, proj_id, test_method, grade_method))






#lock for updating stored data
data_lock = thread.allocate_lock()

#make list of projects
populate_project_list()

#start the threads for grading the projects
main()

#keep the main thread running
while 1:pass
