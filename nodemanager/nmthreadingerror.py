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

# This lets us control the vessels
import nmAPI

EVENT_SCALAR = 0.5 # Scalar number of threads, relative to current
HARD_MIN = 1 # Minimum number of events

# Updates the restrictions files, to use 50% of the threads
def update_restrictions():
  # Create an internal handler function, takes a resource line and returns the new number of threads
  def _internal_func(lineContents):
    try:
      threads = float(lineContents[2])
      threads = threads * EVENT_SCALAR
      threads = int(threads)
      threads = max(threads, HARD_MIN) # Set a hard minimum
      return threads
    except:
      # On failure, return the minimum
      return HARD_MIN
      
  
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
  # Make a log of this
  servicelogger.log("[ERROR]:A Repy vessel has exited with ThreadErr status. Patching restrictions and reseting all vessels.")
  
  # First, update the restrictions
  update_restrictions()
  
  # Then, restart the vessels
  # Get all the vessels
  vessels = nmAPI.vesseldict.keys()
  
  # Reset each vessel
  for vessel in vessels:
    try:
      nmAPI.resetvessel(vessel)
    except Exception, exp:
      # Forge on, regardless of errors
      servicelogger.log("[ERROR]:Failed to reset vessel (Handling ThreadErr). Exception: "+str(exp))
