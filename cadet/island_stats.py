"""
Author: Armon Dadgar
Description:
  This module is designed to work in conjunction with virt_island, and provides
  methods of extracting performance information from an island object.
"""

# Import the priority queue class
dy_import_module_symbols("priority_queue")

# Get some of the important symbols
virt_island = dy_import_module("virt_island")
_context["TOTALED_RESOURCES"] = virt_island.TOTALED_RESOURCES

# Add some extra constants
ALL_THREADS = "ALL"
API_STOPPED = "Stopped"


# Waits for an island to have no live threads
def join_island(island, poll_period=0.1):
  # Wait until there are no live threads
  while len(island.live_threads) > 0:
    sleep(poll_period)

# Dumps the statistics about an island
def dump_island_stats(island,files=True,sockets=True,threads=True):
  # Print a divider
  print "\n--- Island Summary ---\n"

  # Print the some total numbers
  print "Total threads: "+str(len(island.threads))
  print "Live threads: "+str(len(island.live_threads))
  print "Total files: "+str(len(island.all_files))
  print "Open files: "+str(len(island.open_files))
  print "Total sockets: "+str(len(island.all_sockets))
  print "Open sockets: "+str(len(island.open_sockets))

  if files:
    # Print a divider
    print "\n--- Files ---"

    # Print the files
    for file in island.all_files.keys():
      # Is this file still open
      opened = file in island.open_files

      # Get the statistics
      stats = island.all_files[file]

      if opened:
        status = "Open"
      else:
        status = "Closed"

      print "\nFile:"
      print "  Status: "+status
      print "  Name: "+file
      print "  Bytes Written: "+str(stats["write"])
      print "  Bytes Read: "+str(stats["read"])

  if sockets:
    # Print a divider
    print "\n--- Sockets ---"

    # Print the sockets
    for id in island.all_sockets.keys():
      # Decompose the id
      (type, remoteip, remoteport) = id

      # Is this socket still open, non-sensical for UDP...
      opened = id in island.open_sockets

      # Get the statistics
      stats = island.all_sockets[id]

      if opened:
        status = "Open"
      else:
        status = "Closed"

      print "\nSocket/Message:"
      print "  Status: "+status
      print "  Type: "+ type
      print "  Remote IP: "+remoteip
      print "  Remote Port: "+str(remoteport)
      print "  Bytes sent: "+str(stats["send"])
      print "  Bytes recv: "+str(stats["recv"])

  if threads:
    # Print a divider
    print "\n--- Threads ---"

    # Global sum
    global_sum = dict.fromkeys(TOTALED_RESOURCES,0)

    # Print the threads
    for thread in island.threads.keys():
      # Is th thread still alive
      alive = thread in island.live_threads

      # Get the stats
      stats = island.threads[thread]
    
      if alive:
        status = "Live"
      else:
        status = "Dead"

      print "\nThread:"
      print "  Status: "+status
      print "  Name: "+thread
      
      # Print the totals
      for resource,used in stats['totals'].items():
        # Special handling for CPU
        if resource == "cpu":
          used -= stats['initialcpu']

        print "  Total '"+resource+"': "+str(used)

        # Add to the global sum
        global_sum[resource] +=used

  # If dumping threads is disabled, we still need
  # to generate the global sum
  else:
    # Initialize global_sum to None
    global_sum = None
    
    for thread in island.threads.keys():
      # Copy the fist thread
      if global_sum is None:
        global_sum = island.threads[thread]['totals'].copy()
      
      # Add data from other threads
      else:
        for resource,used in island.threads[thread]['totals'].items():
          global_sum[resource] += used

      # Subtract the initial cpu
      global_sum['cpu'] -= island.threads[thread]['initialcpu']


  print "\n--- Global Sum ---\n"

  for resource,used in global_sum.items():
    print "Total '"+resource+"': "+str(used)


# Generates a single timeline of activity for an island
# inc_stoptimes add's in stop times
# Returns an array of tuples:
# Entry: (thread, (API, TOC, Amount))
def generate_island_timeline(island, inc_stoptimes=False):
  # Create a priority queue
  comb_timeline = PriorityQueue()

  # Store the first and last entry
  first_event = None
  last_event = None

  # Add all of the timeline events, iterate on each thread
  for thread in island.threads:
    # Get the timeline for this thread
    timeline = island.threads[thread]['timeline']
  
    # Check the first and last events
    if first_event is None or timeline[0][1] < first_event[1]:
      first_event = timeline[0]
    if last_event is None or timeline[-1][1] > last_event[1]:
      last_event = timeline[-1]

    # Iterate over each event in the timeline
    for event in timeline:
      # Use the TOC as the priority, value include the thread
      comb_timeline.insert(event[1], (thread,event))

  # Add stoptimes if requested
  if inc_stoptimes:
    # Check for the stoptime logger module
    if "get_stoptimes_on_interval" not in _context:
      raise Exception, "Stoptime_logger module not available! Need 'get_stoptimes_on_interval' function!"

    # Get all the stoptimes between the first and last event
    stoptimes = get_stoptimes_on_interval(first_event[1], last_event[1])

    # Add these to the timeline
    for stoptime in stoptimes:
      time, amount = stoptime
      comb_timeline.insert(time, (ALL_THREADS,(API_STOPPED, time, amount)))


  # Convert to an array
  events = []
  while True:
    next_event = comb_timeline.deleteMinimum()
    if next_event is None:
      break
    events.append(next_event[1])


  # Return the events
  return events



# Dumps the timeline of activity in the island
# Format: TOC, API, Thread name, Amount
def dump_island_timeline(island):
  # Get the timeline including stop times
  events = generate_island_timeline(island, True)

  print "\n--- Island Timeline ---\n"
  print "TOC, Thread, API, Amount"

  # Read from the queue now
  for next_event in events:
    thread, event = next_event
    API, TOC, amount = event

    # Print the info
    if amount is None:
      amount = ""

    print TOC,thread,API,amount



# Searches the timeline of a single thread for an event.
# Returns the index of that event, or the index it should be at if not found.
# The search is based only on the TOC.
def search_thread_timeline_for_event(timeline, event):
  low_index = 0
  high_index = len(timeline)-1
  event_time = event[1]

  while low_index <= high_index:
    current_index = (high_index - low_index) / 2 + low_index
    current_time = timeline[current_index][1]    

    if event_time == current_time:
      return current_index

    elif event_time < current_time:
      high_index = current_index - 1

    else: # Event time > current_time
      low_index = current_index + 1

  # The low index is where it should be
  return low_index


# Time spent keys
TIME_UTIL_KEYS = set(["cpu", "netsend", "fileread", "filewrite",
                      "netrecv", "outsockets", "random",
                      "sleep", "live","stopped"])

# Maps an API call to the time spent category
API_TO_TIME = {
               virt_island.API_SENDMESS:"netsend",
               virt_island.API_FILE_READ:"fileread",
               virt_island.API_FILE_WRITE:"filewrite",
               virt_island.API_SOCK_RECV:"netrecv",
               virt_island.API_SOCK_SEND:"netsend",
               virt_island.API_OPENCONN:"outsockets",
               virt_island.API_RANDOM:"random",
               virt_island.API_SLEEP:"sleep",
               virt_island.API_SETTIMER:"cpu", # settimer uses only CPU
               API_STOPPED:"stopped"
              }

# Generates dictionaries describing the time spent doing
# various activities which utilize resources
def generate_island_time_usage(island):
  # Helper function to commit the time spent and updates the begin time
  def commit_time(thread_dict, TOC):
    resource = thread_dict["resource"]
    thread_dict[resource] += TOC - thread_dict["begin"]
    thread_dict["begin"] = TOC

  # Store the resource limits and usage
  # Usage is stored as resource:(TOC,used amount)
  limits = island.resource_limits
  resource_usage = dict.fromkeys(limits.keys(),(0,0))

  # Get a dictionary to hold all the threads
  thread_usages = {}

  # Create an entry for "all" threads
  total_time = thread_usages[ALL_THREADS] = dict.fromkeys(TIME_UTIL_KEYS,0)

  # Get a timeline of all activities with stoptimes
  timeline = generate_island_timeline(island, True)

  # Process each event
  for event in timeline:
    # Decompose the event
    thread, event_info = event
    API, TOC, amount = event_info


    # If the API is API_STOPPED, then this affects all threads, and
    # must be handled separately
    if API == API_STOPPED:
      # As a first approximation, if the resource being used is "CPU"
      # commit the time up to the stop, and resume after
      resume_time = TOC + amount

      for thread,thread_dict in thread_usages.items():
        # Skip the special combined thread
        if thread == ALL_THREADS:
          continue

        # Skip if the thread is dead
        if thread_dict["created"] == 0 or thread_dict["created"] > TOC:
          continue

        # Get the resource being used
        resource = thread_dict["resource"]

        # Time spent in "cpu" and "outsockets" is not
        # thottled internally by repy, so generic handling
        # of stop and resume applies
        if resource in ["cpu","outsockets"]:
          commit_time(thread_dict, TOC)
          thread_dict["begin"] = resume_time
          thread_dict["stopped"] += amount

        # The use of other resources is throttled by repy internally.
        # This forces us to distinguish between time spent in the call
        # because of being stopped, and time spent due to resource
        # over-use.
        else:
          # Get the thread's timeline
          thread_timeline = island.threads[thread]['timeline']

          # Get the index near being stopped
          stop_index = search_thread_timeline_for_event(thread_timeline, event_info)

          # Get the bracketing events
          before_stop_event = thread_timeline[stop_index-1]
          after_stop_event = thread_timeline[stop_index]
          call_in_progress = before_stop_event[2]

          # This "should" be the case that we are in the middle of an API
          # call. Eg. there should be a "start call file.write" and a 
          # "file.write" immediately afterward.
          if before_stop_event[2] == after_stop_event[0]:
            # We need to determine how long this API call should take
            # in the absense of a stop.
            expected_time = 0

            # If it is a sleep, the time is given explicitly
            if call_in_progress == virt_island.API_SLEEP:
              expected_time = after_stop_event[2] 
            
            # Otherwise, it is based on resource availability
            else:
              # Determine the amount used
              amount_used = resource_usage[thread_dict["resource"]][1]
              amount_used += after_stop_event[2]

              # Determine the over-use
              use_limit = limits[thread_dict["resource"]]
              over_use = amount_used - use_limit

              # Expected sleep time is the time it takes to restore
              # the resources we've overused
              expected_time = max(over_use / use_limit, 0)

            # Determine the actual time spent in the API
            api_start = before_stop_event[1]
            api_end = after_stop_event[1]
            actual_time = api_end - api_start 
       
            # Determine the sum of all the stoptimes during this API call
            all_stops = get_stoptimes_on_interval(api_start, api_end)
            all_stoptimes = 0
            for stop in all_stops:
              TOS, stop_amount = stop
              all_stoptimes += stop_amount


            # NOTE: If the proportion of the stoptime to the actual time is greater than
            # the proportion of the expected time, then attribute this the stopping. 
            # Otherwise, ignore the stop.
            # This is somewhat troublesome, since in some cases the diff_time may be great.
            # E.g. on a sock.recv() there may be no data available. So, the big actual_time is
            # not due to repy throttling, but just blocking waiting for data. In this case, it
            # will cause the "stopped" time to increase, but it is hard to blame anything since
            # that time is not caused by a limited netrecv anyways.
            if all_stoptimes > expected_time:
              # If this is the first stop during this API, we will do all the
              # accounting now
              if all_stops[0][0] == TOC:
                # The amount of time spent on the "resource" is at a minimum
                # the expected time, or the actual_time - stopped_time
                resource_time = max(expected_time, actual_time - all_stoptimes)

                # Add the resource time
                thread_dict[thread_dict["resource"]] += resource_time
                thread_dict["begin"] = api_end
        
                # Make sure everything adds up. If the resource_time is
                # actual_time - stopped_time, then this is just adding the
                # stopped time. Otherwise this is the actual_time - expected_time.
                thread_dict["stopped"] += actual_time - resource_time

          else:
            print "Repy Stopped. Thread in strange state:"
            print thread, " B/A: ",before_stop_event, after_stop_event
            commit_time(thread_dict, TOC)
            thread_dict["begin"] = resume_time
            thread_dict["stopped"] += amount

      # Go to the next event
      continue


    # Check if we have a dictionary for this thread
    if thread in thread_usages:
      thread_dict = thread_usages[thread]
    else: # First time we've seen the thread, setup it's dict
      thread_dict = thread_usages[thread] = dict.fromkeys(TIME_UTIL_KEYS,0)
      thread_dict["started API"] = None


    # Some API's are special. These are island specific, rather than API things.
    # For example, we need to handle THREAD_CREATED, and THREAD_DESTROY
    if API == virt_island.THREAD_CREATED:
      # Store the time the thread was last created
      thread_dict["created"] = TOC

      # Set the current resource being used to "cpu"
      thread_dict["resource"] = "cpu"

      # Set the time that this resource began consumption
      thread_dict["begin"] = TOC

    elif API == virt_island.THREAD_DESTROY:
      # Store the time that the thread was alive
      thread_dict["live"] = TOC - thread_dict["created"]

      # Set created to 0, so we know that this thread is finalized
      thread_dict["created"] = 0

      # Commit the resource use
      commit_time(thread_dict, TOC)


    # Check if an API call is being initiated
    elif API == virt_island.API_START:
      # Commit the time used
      commit_time(thread_dict, TOC)

      # Update the API and resource, amount is overloaded to store
      # the API that is underway.
      thread_dict["started API"] = amount
      thread_dict["resource"] = API_TO_TIME[amount]

      # Restore/Update the resource usage
      if thread_dict["resource"] in resource_usage:
        last_toc, last_usage = resource_usage[thread_dict["resource"]]
        elapsedtime = TOC - last_toc
        resource_regen = elapsedtime * limits[thread_dict["resource"]] 
        if resource_regen > last_usage:
          resource_usage[thread_dict["resource"]] = (TOC, 0)
        else:
          resource_usage[thread_dict["resource"]] = (TOC, last_usage - resource_regen)


    # If one thread issues an exit all, we need to finalize all the threads
    elif API == virt_island.API_EXITALL:
      for thread, thread_dict in thread_usages.items():
        if thread == ALL_THREADS: # Ignore the "fake" thread
          continue

        # If the thread timeline does not end in THREAD_DESTROY,
        # we artificially add it to our timeline to finalize the thread.
        thread_timeline = island.threads[thread]['timeline']
        if thread_timeline[-1][0] != virt_island.THREAD_DESTROY:
          timeline.append((thread,(virt_island.THREAD_DESTROY, TOC, None)))

    else:
      # If the API corresponds to the one that was started,
      # then it completed, and we should commit it.
      if API == thread_dict["started API"] and thread_dict["resource"] != "cpu":
        # Commit the time
        commit_time(thread_dict, TOC)

        # Update the resouce usage
        if thread_dict["resource"] in resource_usage:
          start_toc, last_usage = resource_usage[thread_dict["resource"]]
          resource_usage[thread_dict["resource"]] = (start_toc, last_usage + amount) 

      # Switch the resource to cpu
      thread_dict["started API"] = None
      thread_dict["resource"] = "cpu"
      
  
  # Total all the threads
  for thread,thread_dict in thread_usages.items():
    if thread_dict is total_time:
      continue
    for type in TIME_UTIL_KEYS:
      total_time[type] += thread_dict[type]


  # Return the time usages dict
  return thread_usages


# Dumps the total time spent "doing" things
# E.g. time spent sending data, or reading data, etc.
def dump_island_time_usage(island, show_threads=True):
  # Get the time spent
  thread_usages = generate_island_time_usage(island)
  total_time = thread_usages[ALL_THREADS]

  print "\n--- Thread Time Consumption ---"

  if show_threads:
    for thread, thread_time in thread_usages.items():
      if thread != ALL_THREADS:
        print "\nThread:"
        print "  Name: "+thread
        for type in TIME_UTIL_KEYS:
          if thread_time[type] > 0.0:
            print "  Total '"+type+"': " + str(thread_time[type]) + " (" + str(round(100 * thread_time[type] / thread_time["live"], 2)) + "%)"

  print "\nAll Threads (Global)"

  # Print the global
  for type in TIME_UTIL_KEYS:
    if total_time[type] > 0.0:
      print "  Total '"+type+"': " + str(total_time[type]) + " (" + str(round(100 * total_time[type] / total_time["live"], 2)) + "%)"



