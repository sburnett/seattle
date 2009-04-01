"""
Author: Armon Dadgar
Start Date: March 31st, 2009
Description:
  When a vessel is terminated with the ThreadErr status, this file contains the code necessary to reduce the global
  event limit by 50%, and to restart all vessels that are running.

"""

# Use this for generic processing
import nmrestrictionsprocessor
    
import servicelogger

EVENT_SCALAR = 0.5 # Scalar number of threads, relative to current
HARD_MIN = 1 # Minimum number of events

# Updates the restrictions files, to use 50% of the threads
def update_restrictions():
  # Create an internal handler function, takes a resource line and returns the new number of threads
  def _internal_func(lineContents):
    threads = int(lineContents[2])
    threads = threads * EVENT_SCALAR
    threads = int(threads)
    threads = max(threads, HARD_MIN) # Set a hard minimum
    return threads
  
  # Create a task that uses our internal function
  task = ("resource","events",_internal_func,True)
  taskList = [task]
  
  # Process all the resource files
  errors = nmrestrictionsprocessor.process_all_files(taskList)
  
  # Log any errors we encounter
  if errors != None:
    for e in errors:
      print e
      servicelogger.log("[ERROR]:Unable to patch events limit in resource file "+ e[0] + ", exception " + str(e[1]))

  

def handle_threading_error():
  """
  <Purpose>
    Handles a repy node failing with ThreadErr. Reduces global thread count by 50%.
    Restarts all existing vesselts
  """
  # First, update the restrictions
  update_restrictions()
  
  # Then, restart the vessels
  # TODO
  
