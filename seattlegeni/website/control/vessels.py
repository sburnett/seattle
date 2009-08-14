"""
<Program Name>
  vessels.py

<Started>
  July 16, 2009

<Author>
  Justin Samuel

<Purpose>
  Provides utilities for the controller interface (interface.py) to use for
  performing acquisition of different types of vessels as well as release of
  vessels.
"""

from seattlegeni.common.exceptions import *

from seattlegeni.common.api import backend
from seattlegeni.common.api import lockserver
from seattlegeni.common.api import maindb

from seattlegeni.common.util import log
from seattlegeni.common.util import parallel

from seattlegeni.common.util.decorators import log_function_call





@log_function_call
def acquire_wan_vessels(lockserver_handle, geniuser, vesselcount):
  """
  <Purpose>
    Acquire 'wan' vessels for a geniuser.
  <Arguments>
    lockserver_handle
      The lockserver handle to be used for obtaining node locks.
    geniuser
      The GeniUser the vessels should be acquired for.
    vesselcount
      The number of vessels to acquire.
  <Exceptions>
    UnableToAcquireResourcesError
      If either the user does not not have enough vessel credits to acquire the
      number of vessels they requested or if there are not enough vessels
      available to fulfill the request.
  <Side Effects>
    The vessels are acquired for the user. The database has been updated to
    reflect the acquisition.
  <Returns>
    A list of the vessels that were acquired.
  """
  
  # Get a randomized list of vessels where no two vessels are on the same subnet.
  vessel_list = maindb.get_available_wan_vessels(geniuser, vesselcount)
  
  return _acquire_vessels_from_list(lockserver_handle, geniuser, vesselcount, vessel_list)





@log_function_call
def acquire_lan_vessels(lockserver_handle, geniuser, vesselcount):
  """
  <Purpose>
    Acquire 'lan' vessels for a geniuser.
  <Arguments>
    lockserver_handle
      The lockserver handle to be used for obtaining node locks.
    geniuser
      The GeniUser the vessels should be acquired for.
    vesselcount
      The number of vessels to acquire.
  <Exceptions>
    UnableToAcquireResourcesError
      If either the user does not not have enough vessel credits to acquire the
      number of vessels they requested or if there are not enough vessels
      available to fulfill the request.
  <Side Effects>
    The vessels are acquired for the user. The database has been updated to
    reflect the acquisition.
  <Returns>
    A list of the vessels that were acquired.
  """
  
  # Get a randomized list that itself contains lists of vessels on the same subnet.
  subnet_vessel_list = maindb.get_available_lan_vessels_by_subnet(geniuser, vesselcount)
  
  # This case is a little more involved than with wan or rand vessels. If we
  # fail to get the number of desired vessels from one subnet, we need to try
  # another until we are out of subnets to try.
  for vessel_list in subnet_vessel_list:
    try:
      # If we don't hit an exception and return, then we found a subnet where
      # we could acquire all of the requested vessels. So, we're done.
      return _acquire_vessels_from_list(lockserver_handle, geniuser, vesselcount, vessel_list)
    except UnableToAcquireResourcesError:
      # Try the next subnet.
      continue

  # If we made it here, we tried all subnets in our list.
  raise UnableToAcquireResourcesError





@log_function_call
def acquire_rand_vessels(lockserver_handle, geniuser, vesselcount):
  """
  <Purpose>
    Acquire 'rand' vessels for a geniuser.
  <Arguments>
    lockserver_handle
      The lockserver handle to be used for obtaining node locks.
    geniuser
      The GeniUser the vessels should be acquired for.
    vesselcount
      The number of vessels to acquire.
  <Exceptions>
    UnableToAcquireResourcesError
      If either the user does not not have enough vessel credits to acquire the
      number of vessels they requested or if there are not enough vessels
      available to fulfill the request.
  <Side Effects>
    The vessels are acquired for the user. The database has been updated to
    reflect the acquisition.
  <Returns>
    A list of the vessels that were acquired.
  """
  
  # Get a randomized list of vessels where there are no guarantees about whether
  # the list includes wan vessels, lan vessels, vessels on the same subnet, etc.
  vessel_list = maindb.get_available_rand_vessels(geniuser, vesselcount)
  
  return _acquire_vessels_from_list(lockserver_handle, geniuser, vesselcount, vessel_list)





@log_function_call
def _acquire_vessels_from_list(lockserver_handle, geniuser, vesselcount, vessel_list):
  """
  This function will try to acquire vesselcount vessels from vessel_list.
  If less than vesselcount can be acquired, then the partial set of
  vessels that were acquired will be released by this function before it
  returns.
  
  Returns the list of acquired vessels if successful.
  """
  
  # Make sure there are sufficient vessels to even try to fulfill the request.
  if len(vessel_list) < vesselcount:
    raise UnableToAcquireResourcesError("There are not enough available vessels to fulfill the request.")
  
  acquired_vessels = []

  remaining_vessel_list = vessel_list[:]

  # Keep trying to acquire vessels until there are no more left to acquire.
  # There's a "return" statement in the loop that will get out of the loop
  # once we've obtained all of the vessels we wanted, so here we are only
  # concerned with there being any vessels left to try.
  while len(remaining_vessel_list) > 0:
  
    # Each time through the loop we'll try to acquire the number of vessels
    # remaining that are needed to fulfill the user's request.
    remaining_needed_vesselcount = vesselcount - len(acquired_vessels)
    next_vessels_to_acquire = remaining_vessel_list[:remaining_needed_vesselcount]
    remaining_vessel_list = remaining_vessel_list[remaining_needed_vesselcount:]
  
    # Note that we haven't worried about checking if the number of remaining
    # vessels could still fulfill the user's request. In the name of
    # correctness over efficiency, we'll let this case that should be rare
    # (at least until the vesselcount's users are request get to be huge)
    # sort itself out with a few unnecessary vessel acquisition before they
    # ultimately get released after this loop.
  
    parallel_results = _parallel_acquire_vessels_from_list(lockserver_handle, geniuser, next_vessels_to_acquire)
  
    # The "exception" key contains a list of tuples where the first item of
    # the tuple is the vessel object and the second item is the str(e) of
    # the exception. Because the repy parellelization module that is used
    # underneath only passes up the exception string, we have made
    # _do_acquire_vessel() include the string "UnableToAcquireResourcesError"
    # in the exception message so we can tell these apart from more
    # serious failures (e.g the backed is down).
    for (vessel, exception_message) in parallel_results["exception"]:
      
      if "UnableToAcquireResourcesError" in exception_message:
        # This is ok, maybe the node is offline.
        log.info("Failed to acquire vessel: " + str(vessel))
        
      elif "UnableToAcquireResourcesError" not in exception_message:
        # Something serious happened, maybe the backend is down.
        raise InternalError("Unexpected exception occurred during parallelized " +
                            "acquisition of vessels: " + exception_message)
    
    # The "returned" key contains a list of tuples where the first item of
    # the tuple is the vessel object and the second is the return value
    # (which is None).
    for (vessel, ignored_return_value) in parallel_results["returned"]:
      # We successfully acquired this vessel.
      acquired_vessels.append(vessel)

    # If we've acquired all of the vessels the user wanted, we're done.
    if len(acquired_vessels) == vesselcount:
      log.info("Successfully acquired vessel: " + str(vessel))
      return acquired_vessels

  # If we got here, then we didn't acquire the vessels the user wanted. We
  # release these vessels rather than leave the user with a partial set of
  # what they requested.
  release_vessels(lockserver_handle, acquired_vessels)

  raise UnableToAcquireResourcesError("Failed to acquire enough vessels to fulfill the request")





@log_function_call
def _parallel_acquire_vessels_from_list(lockserver_handle, geniuser, vessel_list):
  
  node_id_list = []
  for vessel in vessel_list:
    node_id = maindb.get_node_identifier_from_vessel(vessel)
    # Lock names must be unique, and there could be multiple vessels from the
    # same node in the vessel_list. Whether we want to allow acquiring multiple
    # vessels on the same node is a separate issue from the correctness of this
    # part of the code.
    if node_id not in node_id_list:
      node_id_list.append(node_id)

  # Lock the nodes that these vessels are on.
  lockserver.lock_multiple_nodes(lockserver_handle, node_id_list)
  try:
    return parallel.run_parallelized(vessel_list, _do_acquire_vessel, geniuser)
    
  finally:
    # Unlock the nodes.
    lockserver.unlock_multiple_nodes(lockserver_handle, node_id_list)





@log_function_call
def _do_acquire_vessel(vessel, geniuser):
  """
  Perform that actual acquisition of the vessel by the user (through the
  backend) and update the database accordingly if the vessel is successfully
  acquired.

  When an UnableToAcquireResourcesError is raised, the exception message
  will contain the string "UnableToAcquireResourcesError" so that it can be
  seen in the results of a call to repy's parallelization function.  
  """
  
  node_id = maindb.get_node_identifier_from_vessel(vessel)
  
  try:
    vessel = maindb.get_vessel(node_id, vessel.name)
  except DoesNotExistError:
    message = "Vessel no longer exists once the node lock was obtained."
    raise UnableToAcquireResourcesError("UnableToAcquireResourcesError: " + message)
    
  if vessel.acquired_by_user is not None:
    message = "Vessel already acquired once the node lock was obtained."
    raise UnableToAcquireResourcesError("UnableToAcquireResourcesError: " + message)
  
  node = maindb.get_node(node_id)
  if node.is_active is False:
    message = "Vessel's node is no longer active once the node lock was obtained."
    raise UnableToAcquireResourcesError("UnableToAcquireResourcesError: " + message)
  
  # This will raise a UnableToAcquireResourcesException if it fails (e.g if
  # the node is down). We want to allow the exception to be passed up to
  # the caller.
  try:
    backend.acquire_vessel(geniuser, vessel)
  except UnableToAcquireResourcesError, e:
    raise UnableToAcquireResourcesError("UnableToAcquireResourcesError: " + str(e))
  
  # Update the database to reflect the successful vessel acquisition.
  maindb.record_acquired_vessel(geniuser, vessel)
    




@log_function_call
def release_vessels(lockserver_handle, vessel_list):
  """
  <Purpose>
    Release vessels (regardless of which user has acquired them)
  <Arguments>
    lockserver_handle
      The lockserver handle to use for acquiring node locks.
    vessel_list
      A list of vessels to be released.
  <Exceptions>
    None.
  <Side Effects>
    The vessels in the vessel_list are released.
  <Returns>
    None.
  """
    
  for vessel in vessel_list:
    _do_release_vessel(lockserver_handle, vessel)





@log_function_call
def _do_release_vessel(lockserver_handle, vessel):
  """
  Obtains a lock on the node the vessel is on and then makes a call to the
  backend to release the vessel.
  """
  
  node_id = maindb.get_node_identifier_from_vessel(vessel)

  # Lock the vessel.
  lockserver.lock_node(lockserver_handle, node_id)
  try:
    try:
      vessel = maindb.get_vessel(node_id, vessel.name)
    except DoesNotExistError:
      # The vessel record no longer exists, so the vessel must no longer exist.
      return
      
    if vessel.acquired_by_user is None:
      # The vessel must have already been released.
      return
    
    # We don't check for node.is_active == True because we might as well have
    # the backend try to clean up the vessel even if the database says it's
    # inactive (maybe the node is back online?).
    
    # This will not raise an exception, even if the node the vessel is on is down.
    backend.release_vessel(vessel)
    
    # Update the database to reflect the release of the vessel.
    maindb.record_released_vessel(vessel)
    
  finally:
    # Unlock the user.
    lockserver.unlock_node(lockserver_handle, node_id)

