"""
<Program Name>
  node_monitor_log_parser.py

<Started>
  April 14, 2011

<Author>
  Steven Portzer

<Purpose>
  Loads and processes logs created by node_monitor.py.

<Notes>
  The methods in this library use lists and dictionaries containing the
  following two data structures:

    event: a dict which correspond to one line in the node_events.log log
      created by node_monitor.py, has following fields:

      'time': a float value, the time the event occurred
      'location': the location of the node
      'event_type': "advertising", "not_advertising", "contactable", or
        "not_contactable" depending on the sort of event it is
      'name': either the public key name for advertising events or the md5 hash
        of the nodeid for contactability events

    nodedict: corresponds to an entry in node_dicts.log, contains the following:
      'nodeid': the md5 hash of the node's id
      'location': the location of the node
      'version': the version of seattle running on the node
      'time': when the node information was received
      'latency': the time taken to retrieve the information
      'vesseldicts': a list of vessel dictionaries containing 'vesselname',
        'status', 'ownerkey', and 'userkeys' keys. The 'ownerkey' and 'userkeys'
        are hashed using md5 to conserve space and improve human readability.

  An important note is that lists of both events and nodedicts will typically be
  in nondecreasing order by time since the logs are generated in this format and
  all the functions in this library preserve ordering.
"""



def load_nodedicts_from_file(filename):
  """
  <Purpose>
    Returns a list of the nodedicts stored in the log file with the given name.
  <Arguments>
    filename:
      A string giving the name of the file to load nodedicts from. This should
      reference a "node_dicts.log" file created by node_monitor.py.
  <Exceptions>
    An exception will be raised if the filename is invalid or the log is
    improperly formated.
  <Side Effects>
    None.
  <Returns>
    A list of nodedicts.
  """

  logfile = open(filename, 'r')
  logstring = logfile.read()
  logfile.close()
  return load_nodedicts_from_string(logstring)


def load_nodedicts_from_string(logstring):
  """
  <Purpose>
    Returns a list of the nodedicts encoded in the given string.
  <Arguments>
    logstring:
      A string containing the nodedicts to load. This should be the contents of
      a "node_dicts.log" file created by node_monitor.py.
  <Exceptions>
    An exception will be raised if the log is improperly formated.
  <Side Effects>
    None.
  <Returns>
    A list of nodedicts.
  """

  nodedictlist = []

  for line in logstring.split('\n'):

    if line:
      linedata = eval(line)
      nodedictlist.append(linedata)

  return nodedictlist




def load_events_from_file(filename):
  """
  <Purpose>
    Returns a list of the events stored in the log file with the given name.
  <Arguments>
    filename:
      A string giving the name of the file to load events from. This should
      reference a "node_events.log" file created by node_monitor.py.
  <Exceptions>
    An exception will be raised if the filename is invalid or the log is
    improperly formated.
  <Side Effects>
    None.
  <Returns>
    A list of events.
  """

  logfile = open(filename, 'r')
  logstring = logfile.read()
  logfile.close()
  return load_events_from_string(logstring)


def load_events_from_string(logstring):
  """
  <Purpose>
    Returns a list of the events encoded in the given string.
  <Arguments>
    logstring:
      A string containing the events to load. This should be the contents of
      a "node_events.log" file created by node_monitor.py.
  <Exceptions>
    An exception will be raised if the log is improperly formated.
  <Side Effects>
    None.
  <Returns>
    A list of events.
  """

  eventlist = []

  for line in logstring.split('\n'):

    if line:
      linedata = line.split(" ")

      if len(linedata) == 4:
        eventdict = {'time':float(linedata[0]), 'location':linedata[1], \
            'event_type':linedata[2], 'name':linedata[3]}
        eventlist.append(eventdict)
      else:
        raise Exception("improperly formated line: " + line)

  return eventlist




def close_events(eventlist):
  """
  <Purpose>
    Appends additional events to the end of a copy of a list of events,
    guaranteeing that every advertising event will have a corresponding
    not_advertising event and every contactable event will have a corresponding
    not_contactable event. This guarantee is useful for some types of log
    parsing, but the property will fail to hold for nodes which are still
    advertising/contactable when the log terminates.
  <Arguments>
    eventlist:
      A list of events. Due to the way events are matched, you should not pass
      in lists that have been filtered by the 'time' field.
  <Exceptions>
    An exception will be raised if the log contains usual orderings or subsets
    of events not seen in complete node_events.log logs. If this function fails
    for a newly loaded list of events, it's possibly a bug with node_monitor.py.
  <Side Effects>
    None.
  <Returns>
    A list of events containing all the events in eventlist in addition to some
    "not_advertising" and "not_contactable" events appended to the end. The time
    given to the additional events will be the time of the last log entry.
  """

  neweventlist = []

  # This is a set of identifying information for all locations advertising at a
  # given point in the log.
  advertising = set()
  # This is a set of identifying information for all node contactable at a given
  # point in the log.
  contactable = set()

  for event in eventlist:

    # This information should be unique in the sense that only one location/node
    # with this identifier can be advertising/contactable at any given time.
    eventinfo = (event['location'], event['name'])

    if event['event_type'] == "advertising":
      if eventinfo in advertising:
        raise Exception("Pair " + str(eventinfo) + " already advertising!")
      advertising.add(eventinfo)
    elif event['event_type'] == "not_advertising":
      advertising.remove(eventinfo)
    elif event['event_type'] == "contactable":
      if eventinfo in contactable:
        raise Exception("Pair " + str(eventinfo) + " already contactable!")
      contactable.add(eventinfo)
    elif event['event_type'] == "not_contactable":
      contactable.remove(eventinfo)
    else:
      raise Exception("Invalid event type: " + str(event['event_type']))

    neweventlist.append(event)

  endtime = get_last_value(eventlist, 'time')

  # Add a stopped advertising event to the end of the log for any location still
  # advertising.
  for location, name in advertising:
    eventdict = {'time':endtime, 'location':location, \
            'event_type':"not_advertising", 'name':name,}
    neweventlist.append(eventdict)

  # Add a not contactable event to the end of the log for any node still
  # contactable.
  for location, name in contactable:
    eventdict = {'time':endtime, 'location':location, \
            'event_type':"not_contactable", 'name':name,}
    neweventlist.append(eventdict)

  return neweventlist




def filter_by_value(inputlist, keystring, valuelist):
  """
  <Purpose>
    Filter out certain entries from a list of events or nodedicts and return
    only those with one of a list of given value for a specific field.
  <Arguments>
    inputlist:
      A list of dicts. Probably a list of events or nodedicts.
    keystring:
      A key contained in all the dicts in the list. See the definitions for
      events and nodedicts at the top of the program for likely values.
    valuelist:
      A list of values the given key can map to. All other values will be
      filtered out from the returned list.
  <Exceptions>
    None.
  <Side Effects>
    None.
  <Returns>
    A list of dicts containing exactly those entires in inputlist for which
    entry[keystring] is in valuelist.
  """

  resultlist = []

  for entry in inputlist:
    if entry[keystring] in valuelist:
      resultlist.append(entry)

  return resultlist


def filter_by_range(inputlist, keystring, start=None, end=None):
  """
  <Purpose>
    Filter out certain entries from a list of events or nodedicts and return
    only those with a field within a certain range. This is mostly just useful
    for time measurements.
  <Arguments>
    inputlist:
      A list of dicts. Probably a list of events or nodedicts.
    keystring:
      A key contained in all the dicts in the list. See the definitions for
      events and nodedicts at the top of the program for likely values.
    start:
      If specified, all entries where keystring maps to a value less than start
      will be filtered out of the returned list.
    end:
      If specified, all entries where keystring maps to a value greater than
      end will be filtered out of the returned list.
  <Exceptions>
    None.
  <Side Effects>
    None.
  <Returns>
    A list of dicts containing exactly those entires in inputlist for which
    entry[keystring] within the range defined by start and end.
  """

  resultlist = []

  for entry in inputlist:
    if (start is None or entry[keystring] >= start) and \
        (end is None or entry[keystring] <= end):
      resultlist.append(entry)

  return resultlist


def group_by_value(inputlist, keystring):
  """
  <Purpose>
    Aggregate a list of events or nodedicts by the value of a specific field.
  <Arguments>
    inputlist:
      A list of dicts. Probably a list of events or nodedicts.
    keystring:
      A key contained in all the dicts in the list. See the definitions for
      events and nodedicts at the top of the program for likely values.
  <Exceptions>
    None.
  <Side Effects>
    None.
  <Returns>
    A dict of lists of dicts. Maps values of the keystring field for entries in
    inputlist to lists of dicts in inputlist that map keystring to that value.
  """

  resultdict = {}

  for entry in inputlist:

    if entry[keystring] in resultdict:
      resultdict[entry[keystring]].append(entry)
    else:
      resultdict[entry[keystring]] = [entry]

  return resultdict


def group_by_node(eventlist):
  """
  <Purpose>
    Aggregate a list of events by node. Each list in the returned dict will
    contain both contactability and advertising events for the given node.
    Doing this is kind of messy due to special cases, so this function is
    provided for calculating a reasonable partition of events.
  <Arguments>
    eventlist:
      A list of events. Due to the way events are grouped, you should not pass
      in lists that have been filtered by the 'time' field.
  <Exceptions>
    None.
  <Side Effects>
    None.
  <Returns>
    A tuple (nodeeventlistdict, uncontactableeventlist). Nodeeventlistdict is a
    dict of lists of events that maps md5 hashes of nodeids to lists of events
    for that node. Uncontactableeventlist is a list of advertising events for
    all the locations that were never contactable, and can probably be discarded
    unless you are specifically interested in those sorts of events.
  """

  uncontactableeventlist = []
  nodeeventlistdict = {}
  advertisingdict = {}

  # Initialize the list of node events with an empty list for each node.
  for event in eventlist:
    if event['event_type'] == "contactable":
      nodeeventlistdict[event['name']] = []

  # Get a list of 'non_contactable' events grouped by node to aid in determining
  # which node each advertising event corresponds to.
  notcontactabledict = group_by_value(
      filter_by_value(eventlist, 'event_type', ['not_contactable']),
      'location')

  for event in eventlist:

    # Contactability events are trivial to group by node.
    if event['event_type'] in ["contactable", "not_contactable"]:
      nodeeventlistdict[event['name']].append(event)

    # For newly advertising locations, use the current node (or next node if
    # there is no current one) to be contactable at that location. If only one
    # node uses this location this gives the right answer, and if more than one
    # node uses the location this is a very reasonable guess.
    elif event['event_type'] == "advertising":

      if event['location'] in notcontactabledict:
        notcontactablelist = notcontactabledict[event['location']]
      else:
        notcontactablelist = []

      while len(notcontactablelist) > 1 and \
          notcontactablelist[0]['time'] < event['time']:
        notcontactablelist = notcontactablelist[1:]

      if notcontactablelist:
        nodeid = notcontactablelist[0]['name']
      else:
        nodeid = None

      if nodeid is None:
        uncontactableeventlist.append(event)
      else:
        nodeeventlistdict[nodeid].append(event)

      eventinfo = (event['location'], event['name'])
      advertisingdict[eventinfo] = nodeid

    # For locations stopping advertising, we want to retrieve where we put the
    # matching starting advertising event and attach this event to the same node.
    elif event['event_type'] == "not_advertising":
      eventinfo = (event['location'], event['name'])
      nodeid = advertisingdict.pop(eventinfo)

      if nodeid is None:
        uncontactableeventlist.append(event)
      else:
        nodeeventlistdict[nodeid].append(event)

    else:
      raise Exception("Invalid event type: " + str(event['event_type']))

  return (nodeeventlistdict, uncontactableeventlist)




def get_advertising(eventlist, timestamp):
  """
  <Purpose>
    Returns all the locations advertising at a specified time.
  <Arguments>
    eventlist:
      A list of events. Due to the way events are matched, you should not pass
      in lists that have been filtered by the 'time' field.
    timestamp:
      The time for which to get the list of advertising locations.
  <Exceptions>
    None.
  <Side Effects>
    None.
  <Returns>
    A list of 'location' fields for the advertising locations.
  """

  advertisingset = set()

  for event in eventlist:

    if event['time'] > timestamp:
      break
    
    eventinfo = (event['location'], event['name'])

    if event['event_type'] == "advertising":
      advertisingset.add(eventinfo)
    elif event['event_type'] == "not_advertising":
      advertisingset.remove(eventinfo)

  resultset = set()

  for eventinfo in advertisingset:
    resultset.add(eventinfo[0])

  return list(resultset)


def get_contactable(eventlist, timestamp):
  """
  <Purpose>
    Returns all the nodes contactable at a specified time.
  <Arguments>
    eventlist:
      A list of events. Due to the way events are matched, you should not pass
      in lists that have been filtered by the 'time' field.
    timestamp:
      The time for which to get the list of contactable locations.
  <Exceptions>
    None.
  <Side Effects>
    None.
  <Returns>
    A list of nodeid hashes for the contactable nodes.
  """

  contactableset = set()

  for event in eventlist:

    if event['time'] > timestamp:
      break
    
    eventinfo = (event['location'], event['name'])

    if event['event_type'] == "contactable":
      contactableset.add(eventinfo)
    elif event['event_type'] == "not_contactable":
      contactableset.remove(eventinfo)

  resultset = set()

  for eventinfo in contactableset:
    resultset.add(eventinfo[1])

  return list(resultset)




def get_stat_dict(inputdict, statfunc, *args):
  """
  <Purpose>
    Calculates some statistic for all the values in inputdict.
  <Arguments>
    inputdict:
      A dictionary. To use any of the statistic functions in this module, this
      parameter would be dict with lists of events for the values.
    statfunc:
      A function which takes for it's first argument values of the same type as
      The values contained in inputdict.
    *args:
      Any additional arguments will be passed to statfunc after the value for
      inputdict.
  <Exceptions>
    None.
  <Side Effects>
    None.
  <Returns>
    A dict mapping from keys in inputdict to the value of
    statfunc(inputdict[key], *args) for the given key.
  """

  resultdict = {}

  for entry in inputdict:
    resultdict[entry] = statfunc(inputdict[entry], *args)

  return resultdict


def filter_by_stat(statdict, valuelist):
  """
  <Purpose>
    Takes the result of get_stat_dict and filters by the calculated statistic.
  <Arguments>
    statdict:
      A dictionary. Probably one returned by get_stat_dict.
    valuelist:
      A list of values to allow. All other values are filtered out.
  <Exceptions>
    None.
  <Side Effects>
    None.
  <Returns>
    A list of dicts containing exactly those key value pairs in statdict for
    which value is in valuelist.
  """
  resultdict = {}

  for node in statdict:
    if statdict[node] in valuelist:
      resultdict[node] = statdict[node]

  return resultdict


def filer_by_stat_range(statdict, start=None, end=None):
  """
  <Purpose>
    Takes the result of get_stat_dict and filters by the calculated statistic.
    Instead of finding specific values, this accepts values within a given range.
  <Arguments>
    statdict:
      A dictionary. Probably one returned by get_stat_dict.
    start:
      If specified, all entries where the value is less than start will be
      filtered out of the returned dict.
    end:
      If specified, all entries where the value is greater than end will be
      filtered out of the returned dict.
  <Exceptions>
    None.
  <Side Effects>
    None.
  <Returns>
    A list of dicts containing exactly those key value pairs in statdict for
    which value is in the specified range.
  """

  resultdict = {}

  for node in statdict:
    if (start is None or statdict[node] >= start) and \
        (end is None or statdict[node] <= end):
      resultdict[node] = statdict[node]

  return resultdict


def group_by_stat(statdict):
  """
  <Purpose>
    Takes the result of get_stat_dict and aggregates like values together.
  <Arguments>
    statdict:
      A dictionary. Probably one returned by get_stat_dict.
  <Exceptions>
    None.
  <Side Effects>
    None.
  <Returns>
    A dict mapping from values in statdict to lists of keys that map to that
    value.
  """

  resultdict = {}

  for node in statdict:

    if statdict[node] in resultdict:
      resultdict[statdict[node]].append(node)
    else:
      resultdict[statdict[node]] = [node]

  return resultdict


def sort_by_stat(statdict):
  """
  <Purpose>
    Takes the result of get_stat_dict and sorts the keys by their value.
  <Arguments>
    statdict:
      A dictionary. Probably one returned by get_stat_dict.
  <Exceptions>
    None.
  <Side Effects>
    None.
  <Returns>
    A list which sorts keys in statdict according to the natural ordering of
    their corresponding values.
  """

  def compare(x, y):
    if statdict[x] > statdict[y]:
      return 1
    elif statdict[x] < statdict[y]:
      return -1
    else:
      return 0

  nodelist = statdict.keys()
  nodelist.sort(compare)

  return nodelist




# The remaining functions may be useful on their own, but are intended to be
# passed into get_stat_dict as the statfunc parameter.

# Returns the most recent value of the keystring field for the given list of
# dicts. Inputlist is probably a list of events or nodedicts in this case.
def get_last_value(inputlist, keystring):

  if inputlist:
    return inputlist[-1][keystring]
  else:
    return None

# Returns the most initial value of the keystring field for the given list of
# dicts. Inputlist is probably a list of events or nodedicts in this case.
def get_first_value(inputlist, keystring):

  if inputlist:
    return inputlist[0][keystring]
  else:
    return None

# Returns the total time spent advertising by the nodes in eventlist over the
# period of time ending with endtime. If endtime is unspecified, it will be
# inferred to be the time of the last entry in eventlist.
def get_total_time_advertising(eventlist, endtime=None):
  if endtime is None:
    endtime = get_last_value(eventlist, 'time')

  advertisinglist = filter_by_value(eventlist, "event_type", ["advertising"])
  notadvertisinglist = filter_by_value(eventlist, "event_type", ["not_advertising"])

  total = 0

  for event in notadvertisinglist:
    total += event['time']
  for event in advertisinglist:
    total -= event['time']

  total += endtime*(len(advertisinglist) - len(notadvertisinglist))

  return total

# Returns the total number of times some nodes in eventlist started advertising.
def get_number_times_advertising(eventlist):
  return len(filter_by_value(eventlist, "event_type", ["advertising"]))

# Returns the average time spent between starting and stopping advertising by
# the nodes in eventlist over the period of time ending with endtime.
def get_average_time_advertising(eventlist, endtime=None):
  return get_total_time_advertising(eventlist, endtime) / \
      get_number_times_advertising(eventlist)

# Returns the total time spent contactable by the nodes in eventlist over the
# period of time ending with endtime. If endtime is unspecified, it will be
# inferred to be the time of the last entry in eventlist.
def get_total_time_contactable(eventlist, endtime=None):
  if endtime is None:
    endtime = get_last_value(eventlist, 'time')

  contactablelist = filter_by_value(eventlist, "event_type", ["contactable"])
  notcontactablelist = filter_by_value(eventlist, "event_type", ["not_contactable"])

  total = 0

  for event in notcontactablelist:
    total += event['time']
  for event in contactablelist:
    total -= event['time']

  total += endtime*(len(contactablelist) - len(notcontactablelist))

  return total

# Returns the number of times some nodes in eventlist started being contactable.
def get_number_times_contactable(eventlist):
  return len(filter_by_value(eventlist, "event_type", ["contactable"]))

# Returns the average time spent between starting and stopping being contactable
# by the nodes in eventlist over the period of time ending with endtime.
def get_average_time_contactable(eventlist, endtime=None):
  return get_total_time_contactable(eventlist, endtime) / \
      get_number_times_contactable(eventlist)

