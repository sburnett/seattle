"""
<Author>
  Cosmin Barsan
  
<Purpose>
  script that parses and analyzes a set of cnc client log files, 
  printing statistics about the cache hit and mis rates.
  
<Usage>
  python analyze_exp_lag.py results_directory

  To clarify, this script searches for experiment logs in specified directory, and analyzes all experiments 
  that match the experiment type as different trials of the same experiment
  for example analyze_cncclient_logs.py "myresultdir" "cncexperiment-wan-4-wan-1-1-1*"
  will analyze all experiments that have 4 clients, 1 reg, 1 update, and 1 query server as different
  trials of the same experiment.
"""

import sys
import os
import glob

TRACE_CLIENT_LOG_NAME="cncclientlog"
TRACE_CLIENT_LOG_IP="128.208.3.203"
    
#searches for experiment logs in specified directory, and analyzes all experiments that match the experiment type as different trials of the same experiment
#for example analyze_results_in_data_collection("myresultdir", "cncexperiment-wan-4-wan-1-1-1*") will analyze all experiments that have 4 clients, 1 reg, 1 update, and 1 query server as different trials of the same experiment.
def analyze_results_in_data_collection(results_directory):
  if (results_directory.endswith("/")):
    results_directory=results_directory[:len(results_directory)-1]
    
  matching_dirs = glob.glob(results_directory)
  
  #initialize lists to store log file locations for clients and servers
  clientloglist, serverloglist=[],[]
  
  for matchingdir in matching_dirs:
    clientloglist.extend(glob.glob(matchingdir+"/"+"cncclientlog*"))
    serverloglist.extend(glob.glob(matchingdir+"/"+"cncserver*"))
    
    
  if TRACE_CLIENT_LOG_NAME in clientloglist:
    clientloglist.remove(TRACE_CLIENT_LOG_NAME)
  
  #we now have all the log files, so we may begin to process the data
  
  print "####ANALYZING CLIENT LOGS####"
  
  #we will look through each file and note the times during which the trace address is found in the cache, missed in the cache, and removed from the cache
  cache_miss_times=[]
  cache_hit_times=[]
  address_added_times = []
  address_removed_times=[]
  
  miss_message="cache miss: " + str(TRACE_CLIENT_LOG_IP)
  hit_message="cache hit: " + str(TRACE_CLIENT_LOG_IP)
  add_message= str(TRACE_CLIENT_LOG_IP) + " added to node cache"
  remove_message= str(TRACE_CLIENT_LOG_IP)+" removed from node cache"
  
  #read and fill in the data into the dictionaries
  for fn in clientloglist:
    f=open(fn, 'r')
    line_list = f.readlines()
    f.close()
    
    for line in line_list:
      try:
        timestamp_str,message = line.split(':',1)
        timestamp = float(timestamp_str)
      except Exception, e:
        continue
    
      if(miss_message in line):
        cache_miss_times.append(timestamp)
      elif(hit_message in line):
        cache_hit_times.append(timestamp)
        
      #there is a second variation of the add message we want to detect in the form '<ip>:<port> added to cache'.
      elif((add_message in line) or ((TRACE_CLIENT_LOG_IP in line) and ("added to cache" in line))):
        address_added_times.append(timestamp)
      elif(remove_message in line):
        address_removed_times.append(timestamp)
  print "####DONE ANALYZING CLIENT LOGS####\n"
  
  print "####ANALYZING TRACE LOG####"
  trace_log = matchingdir+"/" + TRACE_CLIENT_LOG_NAME
  reg_complete_time = 0
  last_registration=0
  
  f=open(trace_log, 'r')
  line_list = f.readlines()
  f.close()
    
  for line in line_list:
    try:
      timestamp_str,message = line.split(':',1)
      timestamp = float(timestamp_str)
    except Exception, e:
      continue
    
    if(("TCP Registration successful" in line) and reg_complete_time==0):
      reg_complete_time = timestamp
    elif(("TCP Registration successful" in line) or ("UDP Renew Successful, reply from server = RenewAddressRequestComplete" in line)):
      last_registration = timestamp
      
  if(reg_complete_time==0):
    raise Exception("registration completion line not found")

  print "last registration: " + str(last_registration)
  print "first registration complete: " + str(reg_complete_time)
  print "####DONE ANALYZING TRACE LOG####\n"
  
  ###Analyze the lag
  address_add_lag=[]
  address_remove_lag=[]
  average_add_lag=0
  average_remove_lag = 0
  for time_val in address_added_times:
    lag = time_val - reg_complete_time
    address_add_lag.append(lag)
    average_add_lag+=lag
    
  for time_val in address_removed_times:
    lag = time_val - last_registration
    address_remove_lag.append(lag)
    average_remove_lag+=lag
    
  average_add_lag = average_add_lag/len(address_add_lag)
  if len(address_remove_lag)>0:
    average_remove_lag = average_remove_lag/len(address_remove_lag)
  else:
    average_remove_lag=None
  address_add_lag.sort()
  address_remove_lag.sort()
  
  #also transform the cache miss and hit times in the experiment to be relative to first registration
  cache_miss_times_processed=[]
  cache_hit_times_processed=[]
  for raw_time in cache_miss_times:
    if (raw_time>reg_complete_time and raw_time<last_registration+300):
      cache_miss_times_processed.append(raw_time - reg_complete_time)
  for raw_time in cache_hit_times:
    cache_hit_times_processed.append(raw_time - reg_complete_time)
  cache_miss_times=cache_miss_times_processed
  cache_hit_times=cache_hit_times_processed
  
  print "\nadd lag, average = " + str(average_add_lag)
  print "add lag, median = " + str(address_add_lag[len(address_add_lag)/2])
  print str(address_add_lag)
  
  print "\nremove lag, average = " + str(average_remove_lag)
  print "remove lag, median = " + str(address_remove_lag[len(address_remove_lag)/2])
  print str(address_remove_lag)
  
  print "\ncache misses, count = " + str(len(cache_miss_times))
  print str(cache_miss_times)
  
if __name__ == '__main__':
  
  #ignore the program name as argument
  args = sys.argv[1:]
  
  if len(args)<1:
    print "insufficient arguments, see usage in script header"
  
  analyze_results_in_data_collection(args[0])
  
  