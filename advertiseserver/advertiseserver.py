"""
<Program Name>
  advertiseserver.py

<Started>
  October 30, 2011

<Author>
  Sebastian Morgan (sebass63@uw.edu)

<Purpose>
  A python rendition of the central advertise server to provide a performance 
  benchmark against repy versions.
"""

import socket
import time
import sys
import threading
import datetime
import serialize

# This is the dictionary which holds advertisement associations. Entries will 
# be of the form:
# KEY : [(advertise_val, expiration_time), (")]
data_table = {}

# If enabled at runtime, the server will provide verbose information to stdout.
verbose = False

# The length of time between maintenance thread iterations. (The maintenance 
# thread serves to purge expired advertise entries.)
maintenance_sleep = 10

# This retrieves your outward-facing IP address using a lookup on your 
# hostname. Requires a resolvable hostname.
# local_ip = socket.gethostbyname_ex('ninetailsmm.dyndns.org')[2][0]
local_ip = '128.208.4.96'

# The port over which to receive UDP queries. This is experimental.
udp_port = 11034

# The port over which to receive traditional TCP queries. 10102 is standard.
tcp_port = 10102

# How often should we flush logging data?
logging_frequency = 300 # How about every five minutes?

# File objects
error_log = open("log.errordata", "a")    # Errors that we can't fully resolve should be recorded here.
volume_log = open("log.volume", "a")   # We should use this to record the server's query volume.
time_log = open("log.timedata", "a")     # Information about processing time goes here

# Companion variables for logging
puts_so_far = 0 # The number of PUT queries since the last log.
gets_so_far = 0 # The number of GET queries since the last log.
query_times = [] # Store the query times here.




def _purge_expired_items():
  """
  <Purpose>
    Iterates through the data table and removes all exired entries.

  <Arguments>
    None

  <Exceptions>
    None

  <Side Effects>
    None

  <Returns>
    None
  """
  now = time.time()
  keys = data_table.keys()

  for key in keys:
    num_unique_vals = len(data_table[key])

    # We iterate through in reverse, because otherwise deleting an 
    # entry will cause frivolous edge cases.
    iteration_scheme = range(num_unique_vals)
    iteration_scheme.reverse()

    # value format: (value variable, expiration time)
    for value in iteration_scheme:
      expiration_time = data_table[key][value][1]
      temp_value = data_table[key][value][0] # For logging purposese only.
      if now > expiration_time:
        # The entry is expired.
        del data_table[key][value]
        if len(data_table[key]) == 0:
          del data_table[key]
        if (verbose):
          logstring = str("Entry purged: " + str(key) + ": " + str(temp_value) + "\n")
          _log_with_timestamp(logstring)

  return




def _maintenance_thread():
  """
  <Purpose>
    This thread controls execution of the _purge_expired_items method.
    It ensures that the dictionary is cleaned out at appropriate intervals.

  <Arguments>
    None

  <Exceptions>
    None

  <Side Effects>
    None

  <Returns>
    None
  """
  while True:
    _purge_expired_items()
    time.sleep(maintenance_sleep)

  return




def _log_with_timestamp(logstring, output = "stdout"):
  """
  <Purpose>
    Appends a timestamp to the logging output and prints to the 
    appropriate destination.

  <Arguments>
    logstring (string object)
      The string to be recorded.

    output (string object)
      A string chosen from the following, to indicate which output 
      should be used:

        "stdout" - Prints to the console.

  <Exceptions>
    TypeError occurs if either logstring or output is not a string.

    ValueError occurs if output does not match one of the values in 
               known_output_types.

  <Side Effects>
    None

  <Returns>
    None
  """
  known_output_types = ['stdout', 'volume', 'error', 'time']

  # Some type checking.
  if type(logstring) != type(''):
    raise TypeError("Invalid Input! logstring must be a string!")
  if not type(output) == type(''):
    raise TypeError("Invalid Input! output must be a string!")
  if not output in known_output_types:
    raise ValueError("Invalid Input! output must be a known output type!")

  timestamp = "[" + str(datetime.datetime.today())[:-4] + "]"

  if output == "stdout":
    sys.stdout.write(timestamp)
    sys.stdout.write(logstring)
    sys.stdout.flush()
  elif output == "volume":
    volume_log.write(timestamp)
    volume_log.write(logstring)
    volume_log.flush()
  elif output == "error":
    error_log.write(timestamp)
    error_log.write(logstring)
    error_log.flush()
  elif output == "time":
    time_log.write(timestamp)
    time_log.write(logstring)
    time_log.flush()

  return




def _read_item(key, maxvals=100):
  """
  <Purpose>
    Searches the dictionary for values associated with the given key.

  <Arguments>
    key (type-insensitive, usually string)
      The advertisement key for which we're finding values.

    maxvals
      The maximum number of values to return.

  <Exceptions>
    TypeError will be raised if maxvals is not an integer.

    ValueError will be raised if maxvals is less than one.

  <Side Effects>
    None

  <Returns>
    An array of values taken from the dictionary entry under key. If 
    there are no entries, this method will return an empty array.
  """
  if not type(maxvals) == int:
    raise TypeError("Invalid Input! maxvals must be an integer!")
  if maxvals < 1:
    raise ValueError("Invalid Input! maxvals must be greater than zero!")

  if not key in data_table:
    return []

  values = data_table[key][:maxvals]

  answers = []

  for entry in values:
    answers.append(entry[0])

  return answers




def _insert_item(key, val, time_to_live):
  """
  <Purpose>
    Adds a new entry to the dictionary. If the key/value pair already 
    exists, this delays the expiration time by the difference.

  <Arguments>
    key (type-insensitive, usually string)
      The advertisement key - this should match the dictionary key it is 
      stored under.
    val (type-insensitive)
      The value associated with the advertisement key. A tuple of this and 
      the time to live will be stored in the dictionary under the key.
    time_to_live (integer object)
      The time in seconds for the item to exist in the advertise 
      dictionary. Note that this is not the value stored, rather we store 
      the expiration time.

  <Exceptions>
    TypeError will be raised if time_to_live is not an integer.

  <Side Effects>
    None

  <Returns>
    None
  """
  if not type(time_to_live) == int:
    raise TypeError("Invalid Input! time_to_live must be an integer!")

  duplicate_exists = False
  val_index = -1

  # If there's no key already, we're going to end up putting one in.
  if not key in data_table:
    data_table[key] = []

  if len(data_table[key]) > 0:
    # Then this key already exists. Does the value exist, too?
    for entry in data_table[key]:
      val_index += 1
      # Format of entry is (value, expiration_time)
      if entry[0] == val:
        # We have a pretty clear duplicate.
        duplicate_exists = True
    

  if duplicate_exists:
    # Make sure the new TTL won't end up reducing the entry's lifetime.
    if time.time() + time_to_live > data_table[key][val_index][1]:
      # Update the time to live
      data_table[key][val_index] = (val, time.time() + time_to_live)
  else: # Entry does not exist, so add it.
    data_table[key].append((val, time.time() + time_to_live))

  return




def _handle_request(data):
  """
  <Purpose>
    Process advertisements. This method contains no networking operations, 
    and is largely ported from previous versions of the advertise server.

  <Arguments>
    data (string)
      The packet sent by the client in its (more or less) raw form. This is a 
      string which has yet to be run through serialized.repy's deserialize 
      algorithm. A port of serialize.repy's serialize and deserialize methods 
      has been made locally because this client is intended to be purely 
      written in python.

  <Exceptions>
    Quite a few are possible, these will be populated later.

  <Returns>
    A packet ready for sending to the client who issued the original request.

  <Side Effects>
    None
  """
  global puts_so_far
  global gets_so_far
  global query_times
  # Format of requesttuple: ('PUT'/'GET', key, value, TTLval
  requesttuple = serialize.serialize_deserializedata(data)

  if requesttuple[0] == 'PUT':
    puts_so_far += 1

    ############# START Tons of type checking
    try:
      (key, value, ttlval) = requesttuple[1:]
    except ValueError, e:
      _log_with_timestamp(' > ERROR: Incorrect format for request tuple: ' + str(requesttuple) + "\n")
      return

    if type(key) is not str:
      _log_with_timestamp(' > ERROR: Key type for PUT must be str, not' + str(type(key)) + "\n")
      return

    if type(value) is not str:
      _log_with_timestamp(' > ERROR: Value type must be str, not' + str(type(value)) + "\n")
      return

    if type(ttlval) is not int and type(ttlval) is not long:
      _log_with_timestamp(' > ERROR: TTL type must be int or long, not' + str(type(ttlval)) + "\n")
      return

    if ttlval <=0:
      _log_with_timestamp(' > ERROR: TTL must be positive, not ' + str(ttlval) + "\n")
      return
    ############# END Tons of type checking

    _insert_item(key, value, ttlval)
    _insert_item('%all', value, ttlval)

    return serialize.serialize_serializedata("OK")

  elif requesttuple[0] == 'GET':
    gets_so_far += 1

    ############# START Tons of type checking (similar to above
    try:
      (key, maxvals) = requesttuple[1:]
    except ValueError, e:
      log(' > ERROR: Incorrect format for request tuple: ' + str(requesttuple) + "\n")
      return

    if type(key) is not str:
      log(' > ERROR: Key type for GET must be str, not' + str(type(key)) + "\n")
      return

    if type(maxvals) is not int and type(maxvals) is not long:
      log(' > ERROR: Maximum value type must be int or long, not' + str(type(maxvals)) + "\n")
      return

    if maxvals <=0:
      log(' > ERROR: maxvals; Value type must be positive, not ' + str(maxvals) + "\n")
      return

    ############# END Tons of type checking

    readlist = []
    entries = _read_item(key, maxvals)

    for entry in entries:
      readlist.append(entry)

    return serialize.serialize_serializedata(("OK", readlist))

  return





def _udp_callback():
  # AF_INET - Internet socket
  # SOCK_DGRAM - We're using UDP
  sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  sock.bind((local_ip, udp_port))

  # Slow it down a bit so it doesn't mess with debug output.
  time.sleep(0.005)

  _log_with_timestamp("UDP Callback started, now listening on: " + str(local_ip) + ":" + str(udp_port) + "\n")

  while True:
    try:
      # Perhaps 4096 is excessive. I wonder, is this vulnerable to 
      # overflow attacks?
      data, addr = sock.recvfrom(4096)
  
      _log_with_timestamp("Connection received from: " + str(addr[0]) + ":" + str(addr[1]) + "\n")

      # We don't need to delimit TCP requests in raw python, this is a device of 
      # repy.
      session_request = False
      if '\n' in data:
        data = data.split('\n')[1]
        session_request = True

      # Parallelization is cool, but linearity is easy. Upgrade later.
      # NOTE: addr is a tuple of (IP, port).
      formatted_response = _handle_request(data)

      if session_request:
        formatted_response = str(len(formatted_response)) + "\n" + formatted_response

      sock.sendto(formatted_response, addr)

      _log_with_timestamp("Response sent to: " + str(addr[0]) + ":" + str(addr[1]) + "\n")
    except Exception, e:
      _log_with_timestamp("[UNKNOWN ERROR] " + str(e) + "\n", output='error')




def _tcp_callback():
  # AF_INET - Internet socket
  # SOCK_STREAM - Specify TCP
  sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  sock.bind((local_ip, tcp_port))

  sock.listen(5)

  # Slow it down a bit to prevent messing up our debugging.
  time.sleep(0.005)

  _log_with_timestamp("TCP Callback started, now listening on: " + str(local_ip) + ":" + str(tcp_port) + "\n")

  while True:
    try:
      connection_socket, addr = sock.accept()

      start = time.time()

      connection_socket.settimeout(1.0)

      # Again, 4096 may be excessive.
      data = connection_socket.recv(4096)

      session_request = False
      if '\n' in data:
        data = data.split('\n')[1]
        session_request = True

      formatted_response = _handle_request(data)

      if session_request:
        formatted_response = str(len(formatted_response)) + "\n" + formatted_response

      connection_socket.send(formatted_response)

      connection_socket.close()

      query_times.append(time.time() - start)
    except socket.timeout, e:
      _log_with_timestamp("[TIMEOUT ERROR] " + str(e) + "\n", output='error')
    except Exception, e:
      _log_with_timestamp("[UNKNOWN ERROR] " + str(e) + "\n", output='error')



# helper function, records logging data at specified intervals.
def _flush_logs():
  global puts_so_far
  global gets_so_far
  global query_times
  while True:
    time.sleep(logging_frequency)

    _log_with_timestamp("Total TCP Queries: " + str(puts_so_far + gets_so_far) + "\n", 'volume')
    _log_with_timestamp("  PUT Volume: " + str(puts_so_far) + "\n", 'volume')
    _log_with_timestamp("  GET Volume: " + str(gets_so_far) + "\n", 'volume')

    query_average = 0
    if len(query_times) > 0:
      query_average = sum(query_times) / len(query_times)
    _log_with_timestamp("Query Average: " + str(query_average) + " seconds\n", 'time')

    puts_so_far = 0
    gets_so_far = 0
    query_times = []




def main():
  puts_so_far = 0
  gets_so_far = 0

  _log_with_timestamp("Starting logging thread . . . . . ")
  log_thread = threading.Thread(group=None, target=_flush_logs, name="THREAD-LOG", args = (), kwargs = {})
  log_thread.setDaemon(True)
  log_thread.start()
  sys.stdout.write("[DONE]\n")

  _log_with_timestamp("Creating maintenance thread . . . ")
  maintenance_thread = threading.Thread(group=None, target=_maintenance_thread, name="THREAD-MAINT", args = (), kwargs = {})
  maintenance_thread.setDaemon(True)
  maintenance_thread.start()
  sys.stdout.write("[DONE]\n")

  _log_with_timestamp("Starting UDP callback . . . . . . ")
  udp_thread = threading.Thread(group=None, target=_udp_callback, name="THREAD-UDP", args = (), kwargs = {})
  udp_thread.setDaemon(True)
  udp_thread.start()
  sys.stdout.write("[DONE]\n")

  _log_with_timestamp("Starting TCP callback . . . . . . ")
  tcp_thread = threading.Thread(group=None, target=_tcp_callback, name="THREAD-TCP", args = (), kwargs = {})
  tcp_thread.setDaemon(True)
  tcp_thread.start()
  sys.stdout.write("[DONE]\n")

  # Keep the main thread alive.
  while True:
    time.sleep(1)




if __name__ == "__main__":
  main()
