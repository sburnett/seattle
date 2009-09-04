"""
<Program Name>
  autograder_api.py 

<Started>
  August 29, 2009

<Author>
  Jenn Hanson

<Purpose>
  API for working with Emulab and remote Seattle nodes.
  This is meant to provide simple course-grained methods
  for writing test scripts for Autograder assignments.

"""

#starts an Emulab experiment, sets up the network topology
#with a specified ns file, initializes nm_remote_api to gather stuff on nodes
def start_emulab(ns_filename, experiment_name, project_name):
  """
  <Purpose>
        Starts emulab experiment with the specified ns file.
        Checks that Seattle was started on each of the Emulab nodes.
        Initializes internal logic to keep track of the vessels.
        
  <Arguments>
        ns_filename = filename of the ns file that you want for setting up the network topology
        experiment_name = name of the experiment to be created on Emulab
        projct_name = name of the Emulab project
        
  <Exceptions>
      Raises Exception if there are errors in setting up emulab or if Seattle wasn't found running on any of the Emulab nodes

  <Side Effects>
      Starts an experiment on Emulab.

  <Returns>
      dictionary of....<fill in details later>

  """

def start_new_ns(ns_filename, experiment_name, project_name):
  """
  <Purpose>
      Modifies a previously existing expirament with a new ns file.
      Starts running the new experiment
      Checks that Seattle was started on each of the Emulab nodes
      Initializes internal logic to keep track of the vessels
      
  <Arguments>
      ns_filename = filename of the ns file that you want for setting up the new network topology
        experiment_name = name of the experiment to be created on Emulab
        projct_name = name of the Emulab project
  
  <Exceptions>
      Raises Exception if there are errors in stopping the old experiment, starting the new experiment, or if Seattle wasn't found running on any of the Emulab nodes

  <Side Effects>
      Modifies the experiment running on Emulab.

  <Returns>
      dictionary of...<fill in details later>

  """

#closes the Emulab experiment
def close_emulab(project_name, experiment_name):
  """
  <Purpose>
      Closes an experiment on Emulab so that we can free up resources for them and use the same experiment name again for the next grading session

  <Arguments>
        experiment_name = name of the experiment to be closed on Emulab
        projct_name = name of the Emulab project
  
  <Exceptions>
        Raises an error if the experiment could not be closed properly

  <Side Effects>
        Closes the experiment on emulab

  <Returns>
      Nothing.

  """
    

def put_file_on_vessel(file_name, file_contents, vessel):
  """
  <Purpose>
    Places a file on a vessel
    
  <Arguments>
    file_name = name of the file to be created
    file_contents = stuff to be written to the file to be created
    vessel = longname of vessel on which you want to create the file
  <Exceptions>
    Raises an exception if the vessel was not found or the file could not be creates.

  <Side Effects>
    None.

  <Returns>
    Nothing.

  """

def remove_file_from_vessel(file_name, vessel):
  """
  <Purpose>
    Removes a file that is stored on a vessel

  <Arguments>
      file_name = name of the file you want removed
      vessel = longname of vessel on which you want to remove the file
  
  <Exceptions>
      Raises an exception if the vessel was not found, there was no file with the specified name to be deleted, or the file couldn't be deleted

  <Side Effects>
      None.
      
  <Returns>
      Nothing.

  """    
    

def run_program_on_vessel(vessel, program_name, args, timeout = -1):
  """
  <Purpose>
      Runs a program on a vessel for a specified amount of time.

  <Arguments>
      vessel= longname of vessel you want to run the program on
      program_name = name of the program you want to run --should already be stored on the vessel
      args = string of arguements you want run with the program
      timeout = length of time you want the program to run before forcefully stopping it
                if no timeout is specified it defaults to -1 and runs indefinitely until the program finishes or you stop it from other methods
  
  <Exceptions>
      Raises an exception of the vessel can't be located, if the program isn't found on the vessel, or if the program can't be started

  <Side Effects>
      None.
      
  <Returns>
      Nothing.

  """
  
def stop_running_program_on_vessel(program_name, vessel):
  """
  <Purpose>
    Kills a running program on a vessel

  <Arguments>
    program_name = name of the program to kill
    vessel = longname of the vessel w/ the running program
  
  <Exceptions>
    Raises an exception if the vessel cannot be found, if the program isn't running on the vessel, or if the program can't be killed

  <Side Effects>
    None

  <Returns>
    Nothing
  """
  
def check_if_prog_is_running_on_vessel(program_name, vessel):
  """
  <Purpose>
    Checks if a program is actively running on a vessel

  <Arguments>
    program_name = name of the program to check
    vessel = longname of the vessel to check
  
  <Exceptions>
    Raises an exception if the vessel cannot be found

  <Side Effects>
    None

  <Returns>
    boolean (true == the program is actively running on the vessel)

  """

def get_vessel_log(vessel):
  """
  <Purpose>
    Retrieves the vessel log for a specific vessel

  <Arguments>
    vessel = longname of the vessel
  
  <Exceptions>
    Raises an exception if the vessel cannot be found

  <Side Effects>
    None.

  <Returns>
    

  """
  
def clear_vessel_log(vessel):
  """
  <Purpose>
    Clears the log of a specified vessel

  <Arguments>
    vessel = longname of the vessel
  
  <Exceptions>
    Raises an exception if the vessel cannot be found

  <Side Effects>
    Clears a vessel log

  <Returns>
    Nothing.

  """    




