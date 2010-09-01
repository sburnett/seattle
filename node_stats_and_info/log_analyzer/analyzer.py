#!/usr/bin/python

"""
<Program Name>
  analyzer.py

<Started>
  May 10, 2010

<Author>
  Jeff Rasley
  jeffra45@gmail.com

<Purpose>
  This program is used to analyze software updater and node manager log files.
  It attempts to put each log entry into a unique category that is based on an
  external category dictionary, that is specified by the constant CATEGORIES 
  below.
"""




import os
import sys




# These are the major constants used throughout the program, please make sure 
# these are accurate for your system before using this program.
DATA_PATH = '/home/jeffra45/log_analyzer/node_info/'
CATEGORIES = '/home/jeffra45/log_analyzer/analyzer_categories.dat'

# This list is used throughout the program as well, these are the log file
# names that will be analyzed when analyzing multiple directories of nodes.
LIST_OF_LOGS = ['softwareupdater', 'nodemanager']

# This is used for analyzing Advertise Errors, if we ever add additional
# advertisement sources they will need to be added to this list.
ADVERTISE_TYPES_LIST = ['DHT', 'DOR', 'central']




def analyze_dirs(dir_path, use_last_date=False, custom_timestamp=False):
  """
  <Purpose>
    This is used to analyze all software updater and node manager log files in
    a directory containing a collection of node data. The original intent for
    this method was to be used to traverse through several sub-directories 
    filled with node log files and output category information for each log.
  <Arguments>
    dir_path
      This is a string that indicates the path of the main directory where all
      of the node data lives.
    use_last_date
      This is set to either True or False, depending if the user wants to use
      previously stored timestamp data that indicated the last time a log file
      has been analyzed.
    custom_timestamp
      This can be set to False or a string/float representation of an epoch 
      number.  Any log file that has an epoch timestamp prior to the number 
      given will be ignored from analysis.
  <Exceptions>
    A FileIO related expection may be raised if dir_path or the CATEGORIES
    constant are not pointed at valid locations/files.
  <Side Effects>
    If use_last_date is set to True then a timestamp file is created for the
    specific log file that it's analizing.  The name of this file is of the 
    form, nodemanager.timestamp, and will be overwritten after it has been 
    used with the current time, in epoch form.
  <Returns>
    If this method is run as a library function then it will return a large
    dictionary of dictionaries that looks like the following:

     type: dict       type: dict       type: dict       type: list
     ----------      ------------      ----------      -----------
    |node hases|--->|logfile name|--->|categories|--->|log entries|
     ----------      ------------      ----------      -----------

  """

  # Create a list of node directories based on the main directory path that is
  # passed to analyze_dirs().
  node_dirs_list = os.listdir(dir_path)
  
  # To be filled with keys of node hashes and values of individual analyzed
  # log dicts.
  analyzer_dict = {}

  # We want to make certain choices depending on if we are using this program 
  # as a library or running it from a terminal.
  permit_output =  __name__ == "__main__"

  # Traverses all directories (ie. node directories) in the path that was
  # given and then analyzes each log file (of interest) inside each directory.
  for hashdir in node_dirs_list:

    # Check to make sure we are dealing with a directory. If it is not a
    # directory we want to skip it and move on.
    if not os.path.isdir(dir_path + hashdir):
      continue

    # Initialize the individual log dict for this node hash.
    analyzer_dict[hashdir] = {}

    # Prints out a divider and header information if permitted.
    if permit_output:
      print '--------------------------------'
      print hashdir

    # Traverses through all of the log files listed in the LIST_OF_LOGS 
    # constant and analyzes them individually.
    for logname in LIST_OF_LOGS:
      single_log_dict = {}
      log_path = dir_path + hashdir + '/' + logname

      # Does the actual analysis of the given log file and returns a
      # dictionary with log entry information.
      single_log_dict = analyze_log(log_path, use_last_date, custom_timestamp)
      
      # If permitted we want to print out the statistics about the log file
      # that was just analyzed.
      if permit_output:
        print logname, 'stats:'
        print_single_log_dict(single_log_dict)

        # Print separator between log files as long as this isn't our last 
        # iteration.
        if logname != LIST_OF_LOGS[-1]:
          print '-------------'

      # Store this single log dict into its corresponding dictionary.
      analyzer_dict[hashdir][logname] = single_log_dict

  # If we are executing this program we want to print the results, otherwise 
  # we are using this as a library and want to return the dictionary.
  if not permit_output:
    return analyzer_dict




def analyze_log(logfile_path, use_last_date=False, custom_epochtime=False):
  """
  <Purpose>
    This method is the heart of this program.  It is responsible for doing the
    majority of the log entry analysis.  It takes a single log file and
    attempts to put it into a single unique category.  These categories are 
    based on a dictionary of categories from a data file that must be 
    specified at the top of this program as a constant called CATEGORIES.
  <Arguments>
    logfile_path
      This is a string that indicates the path of the specific log file that 
      will be analyzed.
    use_last_date
      This is set to either True or False, depending on if the user wants to 
      use previously stored timestamp data that indicated the last time a log 
      file was analyzed.
    custom_epochtime
      This can be set to False or a string/float representation of an epoch 
      number.  Any log file that has an epoch timestamp prior to the number 
      given will be ignored from analysis.
  <Exceptions>
    A FileIO related expection may be raised if logfile_path or the CATEGORIES
    constant are not pointed at valid locations/files.
  <Side Effects>
    If use_last_date is set to True then a timestamp file is created for the
    specific log file that it's analyzing.  The name of this file is of the 
    form, nodemanager.timestamp, and will be overwritten, after it has been 
    used, with the current time in epoch form.
  <Returns>
    This will return a dictionary (analyzed_dict) that contains keys of log 
    categories and values that contain lists of log entries.
  """

  # If the log file path is not correct this will raise an exception 
  # indicating it was unable to open the file and the program will quit.
  logfile = open(logfile_path, 'r')

  # If the categories path is not correct this will also raise an exception
  # indication it was unable to open the file and the program will quit.
  cat_fd = open(CATEGORIES, 'r')
  categories_dict = eval(cat_fd.read())
  general_cat_dict = categories_dict['General Categories']
  advertise_cat_list = categories_dict['AdvertiseError Categories']
  cat_fd.close()

  # This is our major data structure that will hold all of our categories with
  # corresponding log entries.
  analyzed_dict = {}

  # Check to see if we want to use any type of timestamp comparison.
  timestamp_filename = logfile.name + '.timestamp'
  if use_last_date and os.path.isfile(timestamp_filename):
    custom_time_fd = open(timestamp_filename, 'r')
    custom_time = eval(custom_time_fd.read())
  elif custom_epochtime:
    # If the string custom_timestamp is not able to be converted to a float a
    # ValueError will be raised and the program will exit. Which is fine
    # because this means that the user did not read the usage of this program.
    custom_time = float(custom_epochtime)
  else:
    custom_time = None
    
  # Store a value for previous timestamp, since we don't have one yet.
  previous_entry_timestamp = None

  # This is the major loop for this method, it traverses the entire log file.
  # The loop has several 'continue's for cases where we either don't need to
  # analyze the entry or something is wrong with the entry.
  for entry in logfile:

    # Convert and store epoch log entry timestamp for later use. If something
    # goes wrong in the conversion we want to flag this entry as having a
    # problem.
    try:
      timestamp = float(entry.split(':')[0])
    except ValueError:
      timestamp = None
      # Log invalid entry in form: log_path, reason, entry, context, cat_dict.
      analyzed_dict = _invalid_entry(logfile.name, 'Invalid Log Entry', entry,
        'Unable to convert timestamp into a float.', analyzed_dict)
      # We found an invalid log entry, it has been categorized, we can move on.
      continue

    # Compare our custom timestamp to the one indicated by this log entry.
    # If our custom timestamp is greater than the current one, there is no
    # need for us to analyze this entry and we can move on.
    if custom_time is not None and timestamp <= custom_time:
      continue

    # Check to see if we have a previous timestamp to check and then check to
    # see if our log file's timestamps are increasing as we traverse them.
    if previous_entry_timestamp and timestamp < previous_entry_timestamp:
      analyzed_dict = _invalid_entry(logfile.name, 'Inconsistent timestamps',
        entry, 'current(' + str(timestamp) + ') is not greater than ' +\
        'previous(' + str(previous_entry_timestamp) + ')', analyzed_dict)

      # If we have found one inconsistent timestamp, chances are there are more
      # inconsistencies in the log file. The log file will need to be reviewed 
      # manually.  From here on out we must disregard all timestamp analysis 
      # so that the category analysis will not be overrun by timestamp
      # inconsistency entries.
      timestamp = 0
      previous_entry_timestamp = 0

      # We have already logged this entry as an invalid entry, we can move on.
      continue

    # Store new previous timestamp for next iteration.
    previous_entry_timestamp = timestamp

    # Check to see if we are dealing with an AdvertiseError entry. If so we
    # need to do do some special analysis that is done in a separate method.
    if entry.find("AdvertiseError occured") > 0:
      analyzed_dict = _analyze_advertise_error(entry, advertise_cat_list,
                                               analyzed_dict, logfile.name)
      # We have now categorized the Advertise Error so we can move on.
      continue

    # Used to store the corresponding category if/when a match is found.  This
    # is useful so that we know the previous category of an entry, which is
    # used to detect entries with multiple matches.
    found = False
    last_match = None

    # Search known categories for log entry match.
    for category in general_cat_dict.keys():
      if entry.find(category) > 0:

        # Has this entry already been categorized? This shouldn't happen, 
        # since categories should be unique, but if it does we want to 
        # categorize it as a problem entry.
        if found:
          analyzed_dict = _invalid_entry(logfile.name, 'The entry has been ' +\
            'tagged with too many categories', entry, 'Category 1: ' +\
            last_match + ', Category 2: ' + category, analyzed_dict)

          # We were forced to categorize this entry as a problem, since a 
          # unique category was not found, we are done and can move on.
          continue
        else:

          # A successful match was found, let's add the entry to its 
          # corresponding category in analyzed_dict.
          key = general_cat_dict[category]
          if analyzed_dict.has_key(key):
            analyzed_dict[key].append(entry)
          else:
            analyzed_dict[key] = [entry]
          found = True
          last_match = category

    # We have searched all known categories and were unable to find a match.
    # The entry must be put into the unknown category in analyzed_dict.
    if not found:
      if analyzed_dict.has_key('unknown'):
        analyzed_dict['unknown'].append(entry)
      else:
        analyzed_dict['unknown'] = [entry]

  # If we are using the timestamp file we want to overwrite it with the most
  # recent timestamp for later use.
  if timestamp is not None and use_last_date:
    timefd = open(logfile.name + '.timestamp','w')
    timefd.write(str(timestamp))
    timefd.close()

  # Log analysis is complete! Let's return to our caller.
  return analyzed_dict




def _analyze_advertise_error(log_entry, category_list, analyzed_dict, log_path):
  """
  <Purpose>
    If an entry contains, "AdvertiseError occurred", it is considered an
    advertise related error and needs further analysis since advertise errors
    can contain multiple errors in one line.
  <Arguments>
    log_entry
      A single log entry to be analyzed, as a string.
    category_list
      A separate category list used specifically to categorize advertise
      errors.
    analyzed_dict
      A dictionary containing all of the categories and their matches so far.
    log_path
      This is used so that we know where this log entry came from, 
      specifically for use if we run across an invalid entry.
  <Exceptions>
    None.
  <Side Effects>
    None.
  <Returns>
    This will return an updated version of the passed in analyzed_dict, that
    will include the categorized advertise error log entry.
  """
  
  # Create a list of the major-types of advertise errors based off of the list
  # of advertise types in the constant ADVERTISE_TYPES_LIST. We change these
  # to be of the type seen in advertise errors, ie. '(type: DHT)'.
  error_major_list = []
  for advertise_type in ADVERTISE_TYPES_LIST:
    error_major_list.append('(type: ' + advertise_type + ')')
  
  # This is the string that is eventually used as the final category for the 
  # log entry in question. We want it to start with AdvertiseError so we know
  # its type.
  final_category = 'AdvertiseError '

  # We want to split the log entry by keyword 'announce error' to check for
  # multiple major type advertise errors. The list 'entry_split' will be of the
  # form: ['timestamp:process id:AdvertiseError', first error, ..., Nth error]
  entry_split = log_entry.split('announce error')

  # We are only concerned with anything after the timestamp, so we are only
  # looking at indices after and including 1.
  for error_entry in entry_split[1:]:
    final_error_tag = final_category

    # Create an unique entry for later use, this is used in case of errors and
    # also used to store into analyzed_dict, if a category is found.
    unique_entry = entry_split[0] + 'announce error' + error_entry

    # Did we break in the middle of looking through the major type list?
    broke_major_loop = False

    # Tag the entry with a major category.
    for error_major in error_major_list:

      # Check to see if we have found a match.
      major_count = error_entry.count(error_major)
      if major_count >= 1:

        # Make sure we haven't found too many matches, we should only find one.
        # If the length of final error tag is different than the original final 
        # category string, then we know we have previously found a match. Thus,
        # we have too many major-tag matches.
        if len(final_error_tag) is not len(final_category) or major_count > 1:
          analyzed_dict = _invalid_entry(log_path, 'Found too many major ' +\
            'categories for an advertise error', log_entry, 'Category 1: ' +\
            final_error_tag + ', Category 2: ' + error_major, analyzed_dict)

          # We have categorized this entry as a problem, we can break out of
          # this inner loop and continue checking the other 'error_entry's by
          # setting broke_major_loop to True.
          broke_major_loop = True
          break
        
        # Good, we found a match! Now lets attach the major category to our 
        # final error tag.  
        final_error_tag += error_major + ": "

    # If for some reason we ran into a problem while traversing the major 
    # category list, we have categorized the entry as a problem and we can 
    # move on to the next error entry.
    if broke_major_loop:
      continue

    # Check to make sure we have found a match.
    if len(final_error_tag) is len(final_category):
      if analyzed_dict.has_key('unknown'):
        analyzed_dict['unknown'].append(unique_entry)
      else:
        analyzed_dict['unknown'] = [unique_entry]
      # Since we were forced to tag this entry as 'unknown' we are done with it
      # and can move onto the next one.
      continue

    # Did we break in the middle of looking through the sub type list?
    broke_sub_loop = False

    # Now we want to check to see what sub-type the error entry is, we need to
    # use our advertise error category list that we opened earlier.
    found_sub_type = False
    for error_sub_type in category_list:
      if error_entry.find(error_sub_type) > 0:
        # If we have already found a sub-type match we need to log this entry
        # as invalid since it has too many matches.
        if found_sub_type:
          analyzed_dict = _invalid_entry(log_path, 'Found too many sub ' +\
            'categories for an advertise error', log_entry, 'Category 1: ' +\
            final_error_tag + ',Category 2: ' + error_sub_type, analyzed_dict)
          broke_sub_loop = True
          break

        # We have found a sub category for this entry, let's attach it to our 
        # final error tag and keep looking for more sub categories.
        found_sub_type = True
        final_error_tag += error_sub_type

    # If for some reason we ran into a problem while traversing the sub- 
    # category list, we have categorized the entry as a problem and we can 
    # move on to the next error entry.
    if broke_sub_loop:
      continue

    # If we haven't found a sub-type we should check our 'timed out' edge case
    # or tag the entry as unknown.
    if not found_sub_type:

      # Check for edge case of 'timed out'. We must search for this phrase
      # last since many other log entries contain it as well and can lead to
      # miscategorization. As an example, a Traceback that was caused because 
      # of a time out issue should be marked differently than a log entry that 
      # just contains the phrase: 'timed out'.
      if error_entry.find('timed out') > 0:
        final_error_tag += error_entry.replace('\n','')

      # We were unable to find a sub-type match so we need to add this entry
      # to our unknown category.
      else:
        if analyzed_dict.has_key('unknown'):
          analyzed_dict['unknown'].append(unique_entry)
        else:
          analyzed_dict['unknown'] = [unique_entry]

          # Since we were forced to tag this entry as 'unknown' we are done 
          # with it and can move onto the next one.
          continue

    # Append our newly created unique entry to our analyzed dictionary with its
    # associated category if it already exists, otherwise create a new entry.
    if analyzed_dict.has_key(final_error_tag):
      analyzed_dict[final_error_tag].append(unique_entry)
    else:
      analyzed_dict[final_error_tag] = [unique_entry]
    
  # We have now added all error entries to our dictionary and can return.
  return analyzed_dict




def _invalid_entry(log_path, reason, entry, context, analyzed_dict):
  """
  <Purpose>
    This method is used to categorize an invalid log entry by putting the
    invalid entry into a 'problems' key in the analyzed_dict.
  <Arguments>
    log_path 
      A string indicating the path to the log file in question.
    reason
      The reason that this entry is considered invalid.
    entry
      The log entry itself.
    context
      Further information about why the entry is invalid.
    analyzed_dict
      The dictionary that we will put the information about the invalid entry.
  <Exceptions>
    None.
  <Side Effects>
    None.
  <Returns>
    This returns a modified analyzed_dict that includes info about the 
    invalid entry.
  """

  # If entry has a \n at the end of it we want to trim it off.
  if entry[-1] == '\n':
    entry = entry[:-1]

  # Construct information about the problem entry, based on information given.
  entry_info = 'Logfile Path: ' + log_path + '\n' + 'Reason: ' + reason +\
               '\nEntry: ' + entry + '\nContext: ' + context

  # Add newly created into to 'problems' key in analyzed_dict and return.
  if analyzed_dict.has_key('problems'):
    analyzed_dict['problems'].append(entry_info)
  else:
    analyzed_dict['problems'] = [entry_info]

  # We are done, we can return to the caller.
  return analyzed_dict




def print_single_log_dict(single_log_dict):
  """
  <Purpose>
    To output a category analysis of a single log file in a form that is easly
    to read and understand.
  <Arguments>
    single_log_dict
      A dictionary containing keys of categories and values that are all lists
      of log entries or information about log entries.
  <Exceptions>
    None.
  <Side Effects>
    None.
  <Returns>
    None.
  """

  max_output = 10
  total_entries = 0

  # We want to print out unknown entries in a special way, so that our 
  # attention is drawn to them.
  if single_log_dict.has_key('unknown'):
    print "\t", len(single_log_dict['unknown']), " unknown log entries found!"
    if len(single_log_dict['unknown']) < max_output:
      for entry in single_log_dict['unknown']:
        print "\t\t", entry
    else:
      print "\tToo many unknown log entries to print!"
      counter = 0
      for entry in single_log_dict['unknown']:
        if counter > 5:
          break
        print '\t\t', entry
        counter += 1
  # Same goes for problem entries, we want to print them out in a similar way
  # as unknown entries.
  if single_log_dict.has_key('problems'):
    print "###"
    print len(single_log_dict['problems']), " problem log entries found!"
    if len(single_log_dict['problems']) < max_output:
      for entry_info in single_log_dict['problems']:
        print entry_info
        if entry_info != single_log_dict['problems'][-1]:
          print "##"
    else:
      print "\tToo many problem entries to print, only printing ", max_output
      counter = 0
      for entry_info in single_log_dict['problems']:
        if counter > max_output:
          break
        print entry_info
        if counter <= max_output:
          print "##"
        counter += 1
    print "###"
  
  # Once we have printed out all of the unknown/problem entries we can now go
  # go about printing out all of the successful categories and their numbers.
  for key in single_log_dict.keys():
    match_num = len(single_log_dict[key])
    if (match_num > 0):
      print  '\t' + str(match_num).zfill(4) + ":\t", key
    total_entries += match_num
  print "\tTotal: ", total_entries




def _print_usage():
  """
  <Purpose>
    This is used to print out the command line usage of this program.
  """

  print "----------------------------------------------------------------------"
  print "analyzer.py [FLAG] [PATH]\n"
  print "-d  [directory]\tAnalyze directory of nodes, looking at all entries."
  print "-dt [directory]\tAnalyze directory of nodes using last stored time."
  print "-dc [timestamp]\tAnalyze directory of nodes using custom epoch time."
  print "-s  [logfile]\tAnalyze single log file, looking at all entries."
  print "-st [logfile]\tAnalyze single log file using last stored time."
  print "----------------------------------------------------------------------"




def main(argv):
  """
  <Purpose>
    This is used to enable this program to be used in various ways from a 
    terminal, as opposed to using it as a library.
  <Arguments>
    argv
      This is used to pass in a list of command line arguments for use when 
      running this program from a terminal, as opposed to as a library.
  <Exceptions>
    None.
  <Side Effects>
    None.
  <Returns>
    None.
  """

  # Check to make sure there are enough arguments.
  if len(argv) is 0:
    print "Needs additional arguments."
    _print_usage()

  # Analyze directories, looking at all entries.
  elif argv[0] == '-d':
    if len(argv) is 2:
      analyze_dirs(argv[1])
    else:
      # Use default path.
      analyze_dirs(DATA_PATH)

  # Analyze directories using last stored timestamps.
  elif argv[0] == '-dt':
    if len(argv) is 2:
      analyze_dirs(argv[1], True)
    else:
      # Use default directory.
      analyze_dirs(DATA_PATH, True)

  # Analyze directory using custom timestamp.
  elif argv[0] == '-dc':
    if len(argv) is 3:
      analyze_dirs(argv[1], False, argv[2])
    else:
      analyze_dirs(DATA_PATH, False, argv[1])

  # Analyze single logfile, looking at all entries.
  elif argv[0] == '-s' and len(argv) is 2:
    print_single_log_dict(analyze_log(argv[1]))

  # Analyze single logfile using last stored timestamp.
  elif argv[0] == '-st' and len(argv) is 2:
    print_single_log_dict(analyze_log(argv[1], True))

  # Analyze single logfile using custom epoch timestamp.
  elif argv[0] == '-sc' and len(argv) is 3:
    print_single_log_dict(analyze_log(argv[1], False, argv[2]))

  # Invalid combination of arguments, print usage.
  else:
    print "Invalid arguments.", argv
    _print_usage()




if __name__ == "__main__":
  main(sys.argv[1:])
