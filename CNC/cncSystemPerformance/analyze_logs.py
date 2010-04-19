"""
<Author>
  Cosmin Barsan
  
<Purpose>
  script that parses and analyzes a set of cnc client log files, 
  printing statistics about the cache hit and mis rates.
  
<Usage>
  python analyze_logs.py results_directory experiment_type

  To clarify, this script searches for experiment logs in specified directory, and analyzes all experiments 
  that match the experiment type as different trials of the same experiment
  for example analyze_cncclient_logs.py "myresultdir" "cncexperiment-wan-4-wan-1-1-1*"
  will analyze all experiments that have 4 clients, 1 reg, 1 update, and 1 query server as different
  trials of the same experiment.
"""

import sys
import os
import glob

#specifes the lifetime of a specified string ip address, entry is a pair of floats.
reg_life=dict()

UDP_HEADER_SIZE=8
TCP_HEADER_SIZE=20
IP_HEADER=20
ETHERNET_HEADER=18

UDP_OVERHEAD= UDP_HEADER_SIZE+IP_HEADER+ETHERNET_HEADER
TCP_OVERHEAD=TCP_HEADER_SIZE+IP_HEADER+ETHERNET_HEADER

def analyze_reg_life(filelist):
  for fn in filelist:
  
    #local ip will be listed in the file before registration is initiated
    local_ip=None
    
    f=open(fn, 'r')
    line_list = f.readlines()
    f.close()
    for line in line_list:
      if "local ip is:" in line:
        timestamp_str, text,local_ip = line.split(':',3)
        local_ip =local_ip.strip()
        
      elif "TCP Registration successful," in line:
        timestamp_str,message = line.split(':',1)
        timestamp = float(timestamp_str)
        
        if local_ip == None:
          raise Exception("node ip not found in logfile before registration completed " + fn)
        
        #lifetime of a node starts when first vessel in it registers 
        if local_ip in reg_life.keys():
          old_start, old_end = reg_life[local_ip]
          if timestamp < old_start:
            reg_life[local_ip] = timestamp, old_end
        else:
          #we do not know when lifetime ends, so we just set it 30 seconds after start for the moment,
          #and change it later when we read the end of the log.
          reg_life[local_ip] = timestamp, (timestamp + 30.0)
        
        #we are done finding the start of the ip reg life
        break
            
    if local_ip == None:
      print "WARNING: node ip not found in logfile " + fn
      continue
        
    if not(local_ip in reg_life.keys()):
      #registration for the vessel never completed
      print "WARNING: registration on " + local_ip + " never completed"
      reg_life[local_ip]= 0,0
      continue
      
    #get the last line, to find the end of the reg life
    last_line = line_list[len(line_list)-1]
    timestamp_str,message = last_line.split(':',1)
    timestamp = float(timestamp_str)
    
    #update the end reglife timestamp
    start, old_end = reg_life[local_ip]
    if(timestamp > old_end):
      reg_life[local_ip] = start, timestamp
      
  return
      
#analyze the cache hit and miss rate for the specified filename, returning a list of statistics
#returns hit_tl, miss_tl, hit_td, miss_td, additional_data
#tl indicates target is live (cache hit or miss occured within target's reg_life)
#tl indicates target is dead (cache hit or miss occured outside target's reg_life)
#additional_data is a dict containing more detailed information
#additional_data["target_age_on_live_misses"] gives a list of times (floats) describing how long the target has been registered, for cases in which a cache miss occured
#additional_data["time_since_taget_death_on_dead_hits"] gives a list of times (floats) describing the number of secconds passed since taget was dead, for cases where  dead hit occurred
def analyze_cache_hit_miss(filename):
  #initialize counters
  hit_tl, miss_tl, hit_td, miss_td= 0,0,0,0
  additional_data = dict()
  additional_data["target_age_on_live_misses"]=[]
  additional_data["time_since_taget_death_on_dead_hits"]=[]
  
  f=open(filename, 'r')
  for line in f:
    try:
      timestamp_str, message = line.split(':', 1)
      timestamp = float(timestamp_str)
    except Exception, e:
      continue
    
    
    message = message.strip()
    
    if (message.startswith("cache hit")):
      junk, ip_and_text=message.split(':',1)
      ip_and_text=ip_and_text.strip()
      target_ip, junk = ip_and_text.split(' ',1) 
      
      if target_ip in reg_life.keys():
        start, end = reg_life[target_ip]
      else:
        #if we have no data available for when the target ip registration is alive, we treat it as if it is always dead
        start, end = 0.0, 0.0
      
      if((timestamp >= start) and (timestamp <= end)):
        #target live case
        hit_tl +=1
        
      else:
        #target dead case
        hit_td +=1
        
        time_since_taget_death = timestamp - end
        additional_data["time_since_taget_death_on_dead_hits"].append(time_since_taget_death)
        
     
    elif (message.startswith("cache miss")):
      junk, ip_and_text=message.split(':',1)
      ip_and_text=ip_and_text.strip()
      target_ip, junk = ip_and_text.split(' ',1)
      
      if target_ip in reg_life.keys():
        start, end = reg_life[target_ip]
      else:
        #if we have no data available for when the target ip registration is alive, we treat it as if it is always dead
        start, end = 0.0, 0.0
      
      if((timestamp >= start) and (timestamp <= end)):
        #target live case
        miss_tl +=1
        
        #save the target age for the cache miss
        target_age = timestamp - start
        additional_data["target_age_on_live_misses"].append(target_age)
      else:
        #target dead case
        miss_td +=1
  
  f.close()
  return hit_tl, miss_tl, hit_td, miss_td, additional_data


#analyze the send and receive rate for a specified log file.
#this works for both client and server log files
#returns the following information in this format: time elapsed, bytes sent, bytes received, tcp bytes sent, tcp bytes received, extra_data
#extra_data contains information about load for specific message types
def analyze_send_receive_load(filename):
  time_elapsed, bytes_sent, bytes_received,tcp_bytes_sent, tcp_bytes_received = 0.0,0,0,0,0
  start_time = -1
  end_time = 0.0
  traffic_end_time= -1
  client_traffic_started = False
  is_client_log = "cncclientlog" in filename
  extra_data = dict()
  extra_data["update_send"]=0
  extra_data["update_receive"]=0
  extra_data["verify_address_request"]=0
  extra_data["verify_address_reply"]=0
  
  f=open(filename, 'r')
  for line in f:
    
    #some log entries do not contain timestamp info, skip such entries
    if(not(": " in line)):
      continue
    
    timestamp_str, message = line.split(':', 1)
    timestamp = float(timestamp_str)
    message = message.strip()
    
    #set start time
    if (start_time==-1):
      start_time = timestamp
    
    #for server logs only, if possible set the start time to the time client traffic starts to hit the servers
    if (not(client_traffic_started) and ("bytes" in message) and not("Announce" in message) and not(is_client_log)):
      start_time = timestamp
      client_traffic_started=True
      
    #for server logs only, if possible set the end time to the time client traffic stops to hit the servers
    if (client_traffic_started and ("bytes" in message) and not("Announce" in message) and not(is_client_log)):
      traffic_end_time = timestamp
    
    #set end time
    end_time = timestamp
    
    #for server logs only
    #ignore entries that occur before client traffic start to avoid skewing of results
    if not(is_client_log) and not(client_traffic_started):
      continue
    
    #check if a packed was sent or received
    if (("bytes" in message) and not("NonCnc" in message)):
      message_components = message.split()
      
      num_bytes = 0
      #get the number of bytes
      for search_index in range(0, len(message_components)):
        if (message_components[search_index].startswith("bytes")):
          num_bytes = int(message_components[search_index-1])
          break
    
      #add to the appropriate counter, and to extra information counters
      if("TCPDataSent" in message_components[0]):
        tcp_bytes_sent += num_bytes + TCP_OVERHEAD
      elif ("TCPDataReceived" in message_components[0]):
        tcp_bytes_received += num_bytes + TCP_OVERHEAD
      elif(message_components[0].endswith("Sent")):
        bytes_sent +=num_bytes + UDP_OVERHEAD
        if("AddressListUpdate" in message_components[1]):
          extra_data["update_send"]+=num_bytes + UDP_OVERHEAD
      elif (message_components[0].endswith("Received")):
        bytes_received += num_bytes + UDP_OVERHEAD
        if("AddressListUpdate" in message_components[1]):
          extra_data["update_receive"]+=num_bytes + UDP_OVERHEAD
  
      if("VerifyAddressRequest" in message_components[1]):
        extra_data["verify_address_request"]+=num_bytes + UDP_OVERHEAD
      elif ("VerifyAddressReply" in message_components[1]):
        extra_data["verify_address_reply"]+=num_bytes + UDP_OVERHEAD
      
      
  if (not(is_client_log) and not(traffic_end_time==-1) and not((traffic_end_time-start_time) == 0)):
    end_time=traffic_end_time
    
  time_elapsed = end_time - start_time
  return time_elapsed, bytes_sent, bytes_received, tcp_bytes_sent, tcp_bytes_received, extra_data


#collect statistics for a list of cncclient log files and print the results
#collects hit and miss rates as well as average load
def analyze_cncclient_log_list(filenames):
  if(len(filenames)<1):
    print "must specify a list of cncclient log files"
    
  print "analyzing registration lifetime of ip addresses in log files..."
  analyze_reg_life(filenames)
  print "analyzing cache hit and miss rates...\n"
  
  #total counters for hit and misses
  hit_tl_total, miss_tl_total, hit_td_total, miss_td_total= 0,0,0,0
  
  #total counters for load
  time_elapsed_total, bytes_sent_total, bytes_received_total = 0.0,0,0
  tcp_bytes_sent_total, tcp_bytes_received_total=0,0
  update_send_total, update_receive_total, verify_address_request_total, verify_address_reply_total = 0,0,0,0
  
  for fn in filenames:
    print "analyzing file " + fn
    hit_tl, miss_tl, hit_td, miss_td, additional_data = analyze_cache_hit_miss(fn)
    total = hit_tl + miss_tl + hit_td + miss_td
    
    #update the cumulative counters
    hit_tl_total+=hit_tl
    miss_tl_total+=miss_tl
    hit_td_total+=hit_td
    miss_td_total+=miss_td
    print "total cache hits/misses = " + str(total)
    if total > 0:
      print "for live target, hits = " + str(hit_tl) + ", rate = " + str(float(hit_tl)/total * 100) + "%"
      print "for live target, misses = " + str(miss_tl) + ", rate = " + str(float(miss_tl)/total * 100) + "%"
      print "for dead target, hits = " + str(hit_td) + ", rate = " + str(float(hit_td)/total * 100) + "%"
      print "for dead target, misses = " + str(miss_td) + ", rate = " + str(float(miss_td)/total * 100) + "%"
    
    print "\n"
    print "list of target ages on live misses: " + str(additional_data["target_age_on_live_misses"])
    print "list of times since taget death on dead_hits: " + str(additional_data["time_since_taget_death_on_dead_hits"])
    print "\n"
    
    time_elapsed, bytes_sent, bytes_received,tcp_bytes_sent, tcp_bytes_received, extra_data = analyze_send_receive_load(fn)
    
    print "time elapsed = " + str(time_elapsed)
    
    if(bytes_sent==0 and bytes_received==0):
      #an error has likely occured in the experiment, resulting in bad data, so exclude it
      print "0 bytes sent and received, excluding this data point as it is likely result of a failed experiment"
      continue
    
    if (time_elapsed>0.0):
      print "cnc bytes sent = " + str(bytes_sent) + ", bytes/sec = " + str(float(bytes_sent)/time_elapsed)
      print "cnc bytes received = " + str(bytes_received) + ", bytes/sec = " + str(float(bytes_received)/time_elapsed)
      print "cnc tcp bytes sent = " + str(tcp_bytes_sent) + ", bytes/sec = " + str(float(tcp_bytes_sent)/time_elapsed)
      print "cnc tcp bytes received = " + str(tcp_bytes_received) + ", bytes/sec = " + str(float(tcp_bytes_received)/time_elapsed)
      
      print "AddressListUpdate load sent = " + str(extra_data["update_send"]) + ", bytes/sec = " + str(float(extra_data["update_send"])/time_elapsed)
      print "AddressListUpdate load received = " + str(extra_data["update_receive"]) + ", bytes/sec = " + str(float(extra_data["update_receive"])/time_elapsed)
      print "VerifyAddress request load = " + str(extra_data["verify_address_request"]) + ", bytes/sec = " + str(float(extra_data["verify_address_request"])/time_elapsed)
      print "VerifyAddress reply load = " + str(extra_data["verify_address_reply"]) + ", bytes/sec = " + str(float(extra_data["verify_address_reply"])/time_elapsed)
      time_elapsed_total+=time_elapsed
      bytes_sent_total+=bytes_sent
      bytes_received_total+=bytes_received
      tcp_bytes_sent_total+=tcp_bytes_sent
      tcp_bytes_received_total+=tcp_bytes_received
      
      update_send_total+=extra_data["update_send"]
      update_receive_total+=extra_data["update_receive"]
      verify_address_request_total+=extra_data["verify_address_request"]
      verify_address_reply_total+=extra_data["verify_address_reply"]
      
  print "Total Stats for all files:"
  total = hit_tl_total + miss_tl_total + hit_td_total + miss_td_total
  print "total hits/misses = " + str(total)
  print "for live target, hits = " + str(hit_tl_total) + ", rate = " + str(float(hit_tl_total)/total * 100) + "%"
  print "for live target, misses = " + str(miss_tl_total) + ", rate = " + str(float(miss_tl_total)/total * 100) + "%"
  print "for dead target, hits = " + str(hit_td_total) + ", rate = " + str(float(hit_td_total)/total * 100) + "%"
  print "for dead target, misses = " + str(miss_td_total) + ", rate = " + str(float(miss_td_total)/total * 100) + "%"
  print "\n"
  print "time elapsed total = " + str(time_elapsed_total)
  if (time_elapsed_total>0.0):
    print "cnc bytes sent total = " + str(bytes_sent_total) + ", bytes/sec = " + str(float(bytes_sent_total)/time_elapsed_total)
    print "cnc bytes received total = " + str(bytes_received_total) + ", bytes/sec = " + str(float(bytes_received_total)/time_elapsed_total)
    print "cnc tcp bytes sent = " + str(tcp_bytes_sent_total) + ", bytes/sec = " + str(float(tcp_bytes_sent_total)/time_elapsed_total)
    print "cnc tcp bytes received = " + str(tcp_bytes_received_total) + ", bytes/sec = " + str(float(tcp_bytes_received_total)/time_elapsed_total)
  
  
  
#collect statistics for a list of log files
#collects load statistics and prints them
def analyze_cncload_from_logs(filenames):
  if(len(filenames)<1):
    print "must specify a list of log files"

  #total counters for load
  time_elapsed_total, bytes_sent_total, bytes_received_total = 0.0,0,0
  tcp_bytes_sent_total, tcp_bytes_received_total=0,0
  update_send_total, update_receive_total, verify_address_request_total, verify_address_reply_total = 0,0,0,0
  
  for fn in filenames:
    print "analyzing file " + fn
    
    time_elapsed, bytes_sent, bytes_received,tcp_bytes_sent, tcp_bytes_received, extra_data = analyze_send_receive_load(fn)
    
    print "time elapsed = " + str(time_elapsed)
    
    if(bytes_sent==0 and bytes_received==0):
      #an error has likely occured in the experiment, resulting in bad data, so exclude it
      print "0 bytes sent and received, excluding this data point as it is likely result of a failed experiment"
      continue
    
    if (time_elapsed>0.0):
      print "cnc bytes sent = " + str(bytes_sent) + ", bytes/sec = " + str(float(bytes_sent)/time_elapsed)
      print "cnc bytes received = " + str(bytes_received) + ", bytes/sec = " + str(float(bytes_received)/time_elapsed)
      print "cnc tcp bytes sent = " + str(tcp_bytes_sent) + ", bytes/sec = " + str(float(tcp_bytes_sent)/time_elapsed)
      print "cnc tcp bytes received = " + str(tcp_bytes_received) + ", bytes/sec = " + str(float(tcp_bytes_received)/time_elapsed)

      print "AddressListUpdate load sent = " + str(extra_data["update_send"]) + ", bytes/sec = " + str(float(extra_data["update_send"])/time_elapsed)
      print "AddressListUpdate load received = " + str(extra_data["update_receive"]) + ", bytes/sec = " + str(float(extra_data["update_receive"])/time_elapsed)
      print "VerifyAddress request load = " + str(extra_data["verify_address_request"]) + ", bytes/sec = " + str(float(extra_data["verify_address_request"])/time_elapsed)
      print "VerifyAddress reply load = " + str(extra_data["verify_address_reply"]) + ", bytes/sec = " + str(float(extra_data["verify_address_reply"])/time_elapsed)
      
      print "\n"
      time_elapsed_total+=time_elapsed
      bytes_sent_total+=bytes_sent
      bytes_received_total+=bytes_received
      tcp_bytes_sent_total+=tcp_bytes_sent
      tcp_bytes_received_total+=tcp_bytes_received
      
      update_send_total+=extra_data["update_send"]
      update_receive_total+=extra_data["update_receive"]
      verify_address_request_total+=extra_data["verify_address_request"]
      verify_address_reply_total+=extra_data["verify_address_reply"]
      
  print "Total Stats for all files:"
  print "time elapsed total = " + str(time_elapsed_total)
  if (time_elapsed_total>0.0):
    print "cnc bytes sent total = " + str(bytes_sent_total) + ", bytes/sec = " + str(float(bytes_sent_total)/time_elapsed_total)
    print "cnc bytes received total = " + str(bytes_received_total) + ", bytes/sec = " + str(float(bytes_received_total)/time_elapsed_total)
    print "cnc tcp bytes sent = " + str(tcp_bytes_sent_total) + ", bytes/sec = " + str(float(tcp_bytes_sent_total)/time_elapsed)
    print "cnc tcp bytes received = " + str(tcp_bytes_received_total) + ", bytes/sec = " + str(float(tcp_bytes_received_total)/time_elapsed)
    print "\n"
    
    
#searches for experiment logs in specified directory, and analyzes all experiments that match the experiment type as different trials of the same experiment
#for example analyze_results_in_data_collection("myresultdir", "cncexperiment-wan-4-wan-1-1-1*") will analyze all experiments that have 4 clients, 1 reg, 1 update, and 1 query server as different trials of the same experiment.
def analyze_results_in_data_collection(results_directory, experiment_type):
  if (results_directory.endswith("/")):
    results_directory=results_directory[:len(results_directory)-1]
    
  matching_dirs = glob.glob(results_directory+"/" + experiment_type)
  
  #initialize lists to store log file locations for clients and servers
  clientloglist, serverloglist=[],[]
  
  for matchingdir in matching_dirs:
    clientloglist.extend(glob.glob(matchingdir+"/"+"cncclientlog*"))
    serverloglist.extend(glob.glob(matchingdir+"/"+"cncserver*"))
    
  #we now have all the log files, so we may begin to process the data
  
  print "####ANALYZING CLIENT LOGS####"
  analyze_cncclient_log_list(clientloglist)
  print "####DONE ANALYZING CLIENT LOGS####\n"
  
  print "####ANALYZING CNC SERVER LOGS####"
  analyze_cncload_from_logs(serverloglist)
  print "####DONE ANALYZING CNC SERVER LOGS####\n"
  
  
  
if __name__ == '__main__':
  
  #ignore the program name as argument
  args = sys.argv[1:]
  
  if len(args)<2:
    print "insufficient arguments, see usage in script header"
  
  analyze_results_in_data_collection(args[0], args[1])
  
  