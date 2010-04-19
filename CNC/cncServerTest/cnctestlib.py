"""
<Author>
  Cosmin Barsan
  
<Purpose>
  Library that provides utility and helper functions for use in cnc tests. 
"""

import sha


#this constant defines how many digits (0-9) the userkey range must cover.
#for instance, if the UPDATE_SERVER_KEYRANGE_SPACE variable is set to 3, hashes of user keys will take values between 0 and 999
UPDATE_SERVER_KEYRANGE_SPACE = 3 

#gets a hash of the specified length for a given string. Used to determine which range a user key falls into
def get_short_hash(arg_string, num_digits = UPDATE_SERVER_KEYRANGE_SPACE):
  sha_obj = sha.new()
  sha_obj.update(arg_string)
  long_hex_result = sha_obj.hexdigest()
  long_int_result = int(long_hex_result, 16)
  short_result = long_int_result%(10**num_digits)
  return short_result
  
  
#for a specified user key, returns a list of update servers or query servers whose key ranges cover the key. returns list of ip,port pairs
#update_key_range_table and query_server_table must be given as parameters
def get_addresses_for_userkey(userkey, update_key_range_table, query_server_table):
  
  #we will add matching addresses to this list
  result_address_list = []
  
  #first check the query_server_table
  if userkey in query_server_table.keys(): 
    #the userkey is in the query server table, meaning it will not be in the update_key_range_table
    #return the list of addresses from the query server table
    return query_server_table[userkey]


  #get the hash of the key to check if there are mathcing update servers.
  key_hash = get_short_hash(userkey)
  
  #for every key range, we check if the hash value is within the range
  for keyrange in update_key_range_table.keys() :
    #if there are no entries under this key range skip it
    if len(update_key_range_table[keyrange])==0:
      continue
      
    lower_bound, upper_bound = keyrange
    
    #check if the key hash falls into the range
    if (lower_bound <= key_hash and key_hash<=upper_bound):
      result_address_list.extend(update_key_range_table[keyrange])
  
  return result_address_list
  
  
#parses the string representation of a update key range dict and returns it in dict form
def parse_update_key_ranges_string(keyrangestring):

  #structure that indicates the update servers with each key range
  #each key is a pair of integers (lower user key, upper user key). Each entry is a list of (ip, port) pairs giving the address of the servers in the respective update unit. 
  update_key_range_table = dict()
  
  #if there are no entries, return empty dict
  if keyrangestring=="None" :
    return update_key_range_table
  
  #split the string to a list of entries
  entries = keyrangestring.split(';')
  
  for entry in entries:
    range_str,addresses_str = entry.split(':')
    lowerboundstr,upperboundstr = range_str.split(',')
    range_value = (int(lowerboundstr), int(upperboundstr))
    
    address_str_list=addresses_str.split('%')
    address_result_list = []
    for address_str in address_str_list:
      ip,port_str = address_str.split(',')
      port = int(port_str)
      address = ip,port
      
      #append the address to the result list for the current entry
      address_result_list.append(address)
      
    #add the entry to the dict
    update_key_range_table[range_value] = address_result_list
    
  return update_key_range_table
  
#parses the string representation of a query table and returns it in dict form
def parse_query_table_string(querytablestring):

  #structure that keeps track of which query servers correspond to a given userkey
  #each key is a userkey of type string. Each entry is a list of (ip, port) pairs giving the address of the servers in the query unit for the particular userkey. 
  query_server_table = dict()
  
  #if there are no entries, return empty dict
  if querytablestring=="None" :
    return query_server_table
  
  #split the string to a list of entries
  entries = querytablestring.split(';')
  
  for entry in entries:
    userkey,addresses_str = entry.split(':')
    
    address_str_list=addresses_str.split('%')
    address_result_list = []
    for address_str in address_str_list:
      ip,port_str = address_str.split(',')
      port = int(port_str)
      address = ip,port
      
      #append the address to the result list for the current entry
      address_result_list.append(address)
      
    #add the entry to the dict
    query_server_table[userkey] = address_result_list
    
  return query_server_table