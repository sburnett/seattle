"""
<Author>
  Cosmin Barsan
  
<Purpose>
  this script is used to estimate load using a specified experiment configuration
  
<Usage>
  Modify values in the first section to specify experiment configuration
  run:
  python estimate_load.py
"""

import time

import sys


BYTES_PER_SIGNATURE = 115
BYTES_PER_PUBLIC_KEY = 38
BYTES_PER_ADDRESS=4+2 #ip+separator+port

UDP_HEADER_SIZE=8
TCP_HEADER_SIZE=20
IP_HEADER=20
ETHERNET_HEADER=18

UDP_OVERHEAD= UDP_HEADER_SIZE+IP_HEADER+ETHERNET_HEADER
TCP_OVERHEAD=TCP_HEADER_SIZE+IP_HEADER+ETHERNET_HEADER

if __name__ == '__main__':
  
  
  number_client_groups= int(sys.argv[1])
  number_clients_per_group= int(sys.argv[2])
  number_userkeys_per_client=1

  number_registration_servers=1
  number_update_keyrange_groups=1 #number of keyrange groups, for example, if set to 2, it means there are two sets fo update servers, each handling one of the key ranges
  number_update_servers_per_keyrange_set=1 #number of update servers in each of the keyrange groups
  number_query_servers=1

  client_churn_rate= number_clients_per_group * .01		#number of occurences in each group where clients join or leave, every 10 minutes
  experiment_duration_in_minutes=30.0	#this information is used to help compute the effect of the initial and final update load on the system
  client_sent_packets_per_2min=120 *1000000 #each client sends this many packets over 2min, assumes traffic is uniformly sentbetween each client and every other client in the group --- send to every node at least every second.   This will always send an query packet when there is a client missing from the group
#  client_sent_packets_per_2min=100 #each client sends this many packets over 2min, assumes traffic is uniformly sentbetween each client and every other client in the group --- send to every node at least every second.   This will always send an query packet when there is a client missing from the group

#  ratio_inactive_nodes = .2 #at any given time, this is the expected ratio of inactive (unregistered) clients in the experiment
  ratio_inactive_nodes = 0.0 #at any given time, this is the expected ratio of inactive (unregistered) clients in the experiment
  
  
  client_groups_managed_by_each_update_server = 1.0* number_client_groups/number_update_keyrange_groups
  number_clients_total = number_client_groups*number_clients_per_group
  number_update_servers_total=number_update_keyrange_groups*number_update_servers_per_keyrange_set
  number_clients_total_expected_active = int((1-ratio_inactive_nodes)*number_clients_total)
  
  update_entry_size_in_keyrange_packet=7.0+1+number_update_servers_per_keyrange_set*BYTES_PER_ADDRESS
  total_update_entry_size_in_keyrange_packet=update_entry_size_in_keyrange_packet*number_update_keyrange_groups
  query_entry_size_in_keyrange_packet = 15.0+1+number_query_servers*BYTES_PER_ADDRESS
  keyrange_request_load_per_client = (23.0+ UDP_OVERHEAD)/(60.0*20) #keyrange requests are sent initially, and only when there is some kind of failure indicating old data is invallid
  keyrange_reply_load_per_client = (UDP_OVERHEAD + 27.0 + total_update_entry_size_in_keyrange_packet +query_entry_size_in_keyrange_packet+BYTES_PER_PUBLIC_KEY+BYTES_PER_SIGNATURE)/(60.0*20)
  
  registration_renew_request_load_per_client = (94.0+UDP_OVERHEAD)/(135.0) 	#94b is avg packet size
  registration_renew_reply_load_per_client = (29.0+UDP_OVERHEAD)/(135.0)	#29b is avg packet size
  
  
  query_update_announcement_load = (168.0 + UDP_OVERHEAD)/(600.0) #168b is avg packet size
  
  #Reg_server_send_load=(keyrange_reply_load_per_client+ registration_renew_reply_load_per_client)* number_clients_total_expected_active + registration_load_from_reg_server_to_update + registration_load_from_reg_server_to_query
  #Reg_server_receive_load=(keyrange_request_load_per_client+ registration_renew_request_load_per_client)* number_clients_total_expected_active + (number_update_servers_total + number_query_servers)*query_update_announcement_load
  Reg_server_send_load=(registration_renew_reply_load_per_client)* number_clients_total_expected_active 
  Reg_server_receive_load=(registration_renew_request_load_per_client)* number_clients_total_expected_active 

  get_addresses_request_load_per_client = (69.0+ UDP_OVERHEAD)/(60.0*30)
  get_addresses_reply_load_per_client = ((UDP_OVERHEAD+17+BYTES_PER_PUBLIC_KEY+BYTES_PER_SIGNATURE+ (BYTES_PER_ADDRESS+8)*number_clients_per_group*(1-ratio_inactive_nodes)))/(60.0*30)
  update_packet_base_size = UDP_OVERHEAD+25+50+38
  
  #compute cost of nodes initially joining and finally leaving in terms of update rate
  full_packets = int(number_clients_per_group*(1-ratio_inactive_nodes))/155
  partial_packet_addresses = int(number_clients_per_group*(1-ratio_inactive_nodes))%155
  full_packet_size = update_packet_base_size+BYTES_PER_ADDRESS*155
  partial_packet_size = update_packet_base_size+BYTES_PER_ADDRESS*partial_packet_addresses #partial packets contain less than 155 addresses
  update_bytes_sent_per_key_on_start = full_packets*full_packet_size + partial_packet_size
  update_packet_send_total_on_start_and_end = 2*4* update_bytes_sent_per_key_on_start  * client_groups_managed_by_each_update_server
  update_packet_send_load_on_start_and_end= update_packet_send_total_on_start_and_end/(experiment_duration_in_minutes*60.0)

  update_packet_send_load_per_update_server=0
  client_churn_rate_per_10sec = client_churn_rate/60.0
  if client_churn_rate==0:
    update_packet_send_load_per_update_server=0
  else:
    #we can fit 155 addresses in a packet
    full_packets = int(client_churn_rate_per_10sec)/155
    partial_packet_addresses = int(client_churn_rate_per_10sec)%155
    full_packet_size = update_packet_base_size+BYTES_PER_ADDRESS*155
    partial_packet_size = update_packet_base_size+BYTES_PER_ADDRESS*partial_packet_addresses #partial packets contain less than 155 addresses
#    print "debug partial size " + str(partial_packet_size)
    single_address_packet_size = update_packet_base_size+BYTES_PER_ADDRESS*1
    #residual packets are usd to account for cases where update packets are sent less frequently than every 10sec
    residual_packet_size = (client_churn_rate_per_10sec-int(client_churn_rate_per_10sec))*single_address_packet_size #this is used to account for cases where churn rate has a decimal
#    print "debug residual size " + str(residual_packet_size)
    total_bytes_sent_in_10sec_span=0
    if(partial_packet_addresses>0):
      total_bytes_sent_in_10sec_span = full_packets*full_packet_size + partial_packet_size + BYTES_PER_ADDRESS*(client_churn_rate_per_10sec-int(client_churn_rate_per_10sec))
    elif(partial_packet_addresses==0):
      total_bytes_sent_in_10sec_span = full_packets*full_packet_size + residual_packet_size  
    update_packet_send_load_per_update_server = 4* total_bytes_sent_in_10sec_span/(10.0)  * client_groups_managed_by_each_update_server
  
  Update_server_send_load = (update_packet_send_load_per_update_server + update_packet_send_load_on_start_and_end)*number_update_servers_total + query_update_announcement_load*number_update_servers_total + get_addresses_reply_load_per_client*min(4,number_clients_per_group)
  #Update_server_receive_load = registration_load_from_reg_server_to_update + get_addresses_request_load_per_client*number_clients_total_expected_active	
  Update_server_receive_load = get_addresses_request_load_per_client*number_clients_total_expected_active	

  query_verify_address_request_packet_size=52.0+UDP_OVERHEAD
  query_verify_address_reply_packet_size=160.0+UDP_OVERHEAD
  packets_resulting_in_cache_misses=int(client_sent_packets_per_2min*ratio_inactive_nodes)
  #packets are sent uniformly, to every other client in the group, 
  #so we can get the approximate number of ip addresses that are inactive by the following
  ip_addresses_inactive = int(number_clients_per_group*ratio_inactive_nodes)
  #in a given two minute timespan, a verify adddress request packet is sent only once for each inactive ip
  verify_inactive_address_request_load_per_client=query_verify_address_request_packet_size*ip_addresses_inactive/(120.0)
  verify_inactive_address_receive_load_per_client=query_verify_address_reply_packet_size*ip_addresses_inactive/(120.0)
  
  #print "debug verify address request load per client" + str(verify_inactive_address_request_load_per_client)
  #print "debug verify address request total" + str(verify_inactive_address_request_load_per_client*number_clients_total_expected_active)
  #print "debug verify address request load per client" + str(verify_inactive_address_receive_load_per_client)
  #print "debug verify address reply total" + str(verify_inactive_address_receive_load_per_client*number_clients_total_expected_active)
  Query_server_send_load=verify_inactive_address_receive_load_per_client*number_clients_total_expected_active+ query_update_announcement_load*number_query_servers
  Query_server_receive_load=verify_inactive_address_request_load_per_client*number_clients_total_expected_active
  #Query_server_receive_load=verify_inactive_address_request_load_per_client*number_clients_total_expected_active+registration_load_from_reg_server_to_query
  
  approx_client_update_send_load = (update_packet_send_load_per_update_server + update_packet_send_load_on_start_and_end)/client_groups_managed_by_each_update_server
  approx_client_update_receive_load = (update_packet_send_load_per_update_server + update_packet_send_load_on_start_and_end)/client_groups_managed_by_each_update_server
  Single_client_send_load=registration_renew_request_load_per_client+keyrange_request_load_per_client+get_addresses_request_load_per_client+verify_inactive_address_request_load_per_client + approx_client_update_send_load
  Single_client_receive_load=registration_renew_reply_load_per_client+keyrange_reply_load_per_client+get_addresses_reply_load_per_client+verify_inactive_address_receive_load_per_client + approx_client_update_receive_load
  
  #tcp registration must be performed by each client initially and every 3600seconds
  reg_packet_request_size=79.0 + TCP_OVERHEAD
  reg_packet_reply_size=46.0 + TCP_OVERHEAD
  Single_client_send_load_tcp = reg_packet_request_size/(3600.0)
  Single_client_receive_load_tcp = reg_packet_reply_size/(3600.0)
  
  Reg_server_send_load_tcp = number_clients_total_expected_active*Single_client_receive_load_tcp
  Reg_server_receive_load_tcp = number_clients_total_expected_active*Single_client_send_load_tcp

  
#  print 'grps c_per_g ser_send ser_recv cli_send cli_recv'
  #print number_clients_total, (Reg_server_send_load + Reg_server_send_load_tcp + Update_server_send_load + Query_server_send_load), (Reg_server_receive_load + Reg_server_receive_load_tcp + Update_server_receive_load + Query_server_receive_load)#, str(Single_client_send_load + Single_client_send_load_tcp), str(Single_client_receive_load+ Single_client_receive_load_tcp)
  print number_clients_total, str(Single_client_send_load + Single_client_send_load_tcp), str(Single_client_receive_load+ Single_client_receive_load_tcp)
