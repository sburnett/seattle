"""
<Program Name>
  make_summary.py

<Started>
  June 2009

<Author>
  n2k8000@u.washington.edu
  Konstantin Pik

<Purpose>
  This file produces summary files and the complete log files from all of the machines
  surveyed.  The log files are collected from their respective directories, and then 
  they are throw into one file. The HTML file is also created via this file.


<Usage>
  python make_sumary.py
  
  Will parse all logs in deploy_logs directory and use time.time() for the timestamp.
"""

import os
import sys

import deploy_html
import deploy_main
import deploy_stats
import deploy_helper
          
          


def build_summary():
  """
  <Purpose>
    This function collects all the important log files from the subdirectories
    and outputs them in a summary.log

  <Arguments>
    None.

  <Exceptions>
    Error opening/creating the log file.

  <Side Effects>
    None.

  <Returns>
    None.
  """

  sep = '---------------------'
  uniq_fn, timestamp = deploy_html.generate_uniq_fn()
  
  # collect all log files into a summary file
  summary_fn = 'detailed.'+uniq_fn
  

  # directory structure is as follows (for the files we want)
  # ./deploy.logs/[remote_host]/deployrun.log
  # ./deploy.logs/[remote_host]/[remote host].deployrun.err.log

  #try:
  # make sure that the dir exists
  if not os.path.isdir('./detailed_logs'):
    os.mkdir('./detailed_logs')
    
  summary_file_handle = open('./detailed_logs/'+summary_fn, 'w')
  
  # states map to #s
  node_states_counter = {}

  # num of states -> to # of occurences
  num_node_states = {}
  
  # has the following keys:
  # SU is running -> how many computers have a SU running
  # NM is running -> how many computers have a NM running
  # SU -> how may computers have just SU running
  # NM -> how many comptuers have just NM running
  # Both SU and NM are running -> how many computers have SU and NM running
  # none -> how many computer have neither SU nor NM running
  su_nm_stats_header = ['SU/NM Info', 'Number of Nodes']
  su_nm_stats = {}
  su_nm_stats['SU is running'] = 0
  su_nm_stats['NM is running'] = 0
  su_nm_stats['Only SU is running'] = 0
  su_nm_stats['Only NM is running'] = 0
  su_nm_stats['SU/NM are not running'] = 0
  su_nm_stats['Both SU and NM are running'] = 0
  
  # will have version that map to # of currently installed
  node_version_dict = {}
  # This'll keep track of the # of not installed computers
  node_version_dict['Not Installed'] = 0
  # This'ss kep track of the node ips/hostnames that have seattle missing
  node_version_dict['Not Installed Node Name'] = []
  
  # this dictionary will be used to build up our html page with all the node 
  # information. the keys to this dictionary are the nodenames, they map to an 
  # array of values which are the values in the table for that node. then 
  # we'll use the deploy_html lib to build up our html tables and write them to the file.
  
  html_dict = {}
  
  # used as the headers for the table built up in html_dict
  html_dict_headers = ['Node Name', 'NodeManager Status', 
      'SoftwareUpdater Status', 'Node Version', 'Node Status', 'Details']
  
  # the html FN that we'll be using
  
  # for every folder in the logs directory  
  for logfolder in os.listdir('./deploy.logs'):
    # each dir should have TWO files (at most), but we only care about one for our 
    # summary file
    # check that it's a directory.
    if os.path.isdir('./deploy.logs/'+logfolder):
      # it's a directory! good! 
      for logfile in os.listdir('./deploy.logs/'+logfolder):
        # now check that each file until we get a file by the name of 
        # 'deployrun.log'
        if os.path.isfile('./deploy.logs/'+logfolder+'/'+logfile):
          # It's a file.. is it the right name?
          errfn = logfolder+'.deployrun.err.log'
          
          if logfile == 'deployrun.log' or logfile == errfn:
            
            
            # Awesome it's the one we want!
            # the logfolder = the remote host (by ip or hostname)
            summary_file_handle.write('\nLog from '+logfolder)

            # make the HTML page. the logfolder is the nodename 
            #deploy_html.html_write('./deploy.logs/'+logfolder+'/'+logfile, logfolder, uniq_fn)
            
            logfile_name = './deploy.logs/'+logfolder+'/'+logfile
            logfile_handle = open(logfile_name, 'r')

            if not os.path.isdir('./detailed_logs/'+logfolder):
              os.mkdir('./detailed_logs/'+logfolder)
              
            detailed_handle = open('./detailed_logs/'+logfolder+'/'+timestamp, 'a')
            
            node_file_as_string = deploy_html.read_whole_file(logfile_handle)
            final_file_content = deploy_helper.summarize_all_blocks(node_file_as_string)
            
            # write to both the files
            summary_file_handle.write(final_file_content)
            detailed_handle.write(final_file_content)
            
                  
            # create a temp array that we'll use to build up the info, and 
            # then throw in to the html_dict
            temp_array = []            
            
            # now check if the node has seattle installed or not
            if deploy_stats.check_is_seattle_installed(node_file_as_string):
              
              # now we need the NM status
              NM_success_status, NM_desc_string, bgcolor  = deploy_stats.check_is_nm_running(node_file_as_string)
              if NM_success_status or NM_desc_string.lower().find('not') == -1:
                su_nm_stats['NM is running'] += 1

              temp_array.append((NM_desc_string, bgcolor))
              
              
              # next we need the SU status
              SU_success_status, SU_desc_string, bgcolor  = deploy_stats.check_is_su_running(node_file_as_string)
              # if it is running then increment the running counter by 1
              if SU_success_status or SU_desc_string.lower().find('not') == -1:
                su_nm_stats['SU is running'] += 1
              temp_array.append((SU_desc_string, bgcolor))
              
              # make sure to record the stats
              # the not is a hack for the high mem usage which returns false
              if SU_desc_string.lower().find('not') == -1 or SU_success_status:
                if NM_desc_string.lower().find('not') == -1 or NM_success_status:
                  # su and nm are running
                  su_nm_stats['Both SU and NM are running'] += 1
                else:
                  # only su is running, nm is not
                  su_nm_stats['Only SU is running'] += 1
              else:
                if NM_desc_string.lower().find('not') == -1 or NM_success_status:
                  # only NM is running
                  su_nm_stats['Only NM is running'] += 1
                else:
                  # neither is running
                  su_nm_stats['SU/NM are not running'] += 1
              
              # now get the node version
              success_status, version_string, bgcolor = deploy_stats.get_node_version(node_file_as_string)
              temp_array.append((version_string, bgcolor))
              
              # keep track of how many of each version/output we have (including errors and upgrades)
              if version_string not in node_version_dict.keys():
                node_version_dict[version_string] = 1
              else:
                node_version_dict[version_string] += 1
              
              
              # and now the node state
              try:
                (success_status, (node_state_array, state_counter), html_color)  = deploy_stats.get_node_state(node_file_as_string)
              except Exception, e:
                (success_status, (node_state_array, state_counter), html_color) = (False, ([], 0), deploy_html.colors_map['Error'])
              
              
              
              # the following chunk of code keeps track of how many nodes have X states on them
              # has # of states | number
              if str(state_counter) in num_node_states.keys():
                # has the key, just get the value and increment by one
                num_node_states[str(state_counter)] = num_node_states[str(state_counter)] + 1
              else:
                # set it to one, and create the key
                num_node_states[str(state_counter)] = 1
              
              # this'll be the string we'll dump to the temp_array.
              
              node_state_success = ''
              for each_vessel in node_state_array:
                # tuple (SuccessState, vesselID, explanation_str)
                if each_vessel[0]:
                  # success!
                  node_state_success += str(each_vessel[2])+','
                  summary_file_handle.write('\nVessel state:\t'+str(each_vessel[1])+':'+str(each_vessel[2]))
                  detailed_handle.write('\nVessel state:\t'+str(each_vessel[1])+':'+str(each_vessel[2]))
                  
                  # This next chunk of code keeps track of what states each nodes are in and how many we have
                  # in that particular state
                  if str(each_vessel[2]) in node_states_counter.keys():
                    node_states_counter[str(each_vessel[2])] = node_states_counter[str(each_vessel[2])] + 1
                  else:
                    node_states_counter[str(each_vessel[2])] = 1
                  
                else:
                  summary_file_handle.write('\nVessel state:\t'+str(each_vessel[1])+':'+str(each_vessel[2]))
                  # don't write the detailed log if we fail.
                
                detailed_handle.write('\n')
                summary_file_handle.write('\n')
                
              if state_counter == 1:
                temp_array.append((node_state_success[0:-1], deploy_html.colors_map['Success']))
              else:
                if state_counter == 0:
                  if node_state_array:
                    # if the array isn't null we have some msg to print, otherwise it's an error
                    temp_array.append((node_state_array[0], deploy_html.colors_map['Error']))
                  else:
                    temp_array.append(('Did not get vesseldict', deploy_html.colors_map['Error']))
                  # no keys on the node, print the human-friendly version (also could be an unknown key)
                  

                  #temp_array.append(('No node-state keys found', deploy_html.colors_map['Error']))
                  
                #else: # state_counter > 1:
                  #temp_array.append(('Multiple states on node!', deploy_html.colors_map['Error']))
              
              # end getting the node state here

            else: # no seattle installed!            
              temp_array = ['', '', '', ('Seattle is not installed', deploy_html.colors_map['Warning'])]
              node_version_dict['Not Installed'] = node_version_dict['Not Installed'] + 1
              # mark the node as not having seattle installed, we'll write a 
              # file that'll have all the missing seattle installs on the nodes
              # also, logfolder is the name of the node.
              node_version_dict['Not Installed Node Name'].append(logfolder)

            html_link = deploy_html.make_link_to_detailed(logfolder, uniq_fn)
            temp_array.append(html_link)            
            # add what we have to the html_dict
            html_dict[logfolder] = temp_array

            

                  
            if os.path.isfile('./deploy.logs/controller.log'):
              deploy_main.shellexec2('cp ./deploy.logs/controller.log ./detailed_logs/controller.'+timestamp)

            if os.path.isfile('./deploy.logs/deploy.err.log'):
              deploy_main.shellexec2('cp ./deploy.logs/deploy.err.log ./detailed_logs/deploy.err.'+timestamp)              
            
            logfile_handle.close()
            detailed_handle.close()

            summary_file_handle.write('\n'+sep+'\n')
  #except Exception, e:
  #  print e
  #finally:
  summary_file_handle.close()
  
  # this'll generate the actual html files from the tables and dicts
  
  # this generates the node-states table
  html_node_states_counter = deploy_html.html_table_from_dict(node_states_counter, ['Node State', 'Number of nodes'])
  
  # this generates the number of nodes in each state table
  html_num_states = deploy_html.html_table_from_dict(num_node_states, ['Number of states', 'Occurence of said number of keys'])
  
  # this generates the table of nm/su stats (X running NM, Y running SU, etc)
  html_su_nm_stats = deploy_html.html_table_from_dict(su_nm_stats, su_nm_stats_header)
  
  # this generates the table with the version breakdown
  html_version_info = deploy_html.html_table_from_dict(node_version_dict, ['Node Version', 'Number of nodes'])
  
  # this generates the main table of nodes and infos.
  html_main_table = deploy_html.html_table_from_dict2(html_dict, html_dict_headers)
  
  # write to a file the clean nodes (nodes where seattle is not installed)
  try:
    # this is the file we'll write to
    empty_nodes_fh = open('missing.list', 'w+')
    # for each node...
    for each_node in node_version_dict['Not Installed Node Name']:
      # write it to file
      empty_nodes_fh.write(str(each_node)+'\n')
    # close the filehandle
    empty_nodes_fh.close()
  except Exception, e:
    print 'Error while trying to write missing.list in make_summary'
    print e
    
  
  # write the html to a file
  deploy_html.html_write(uniq_fn, html_main_table)
  
  # add the following stuff to the top of the file
  deploy_html.html_add_to_top(uniq_fn, html_node_states_counter)
  deploy_html.html_add_to_top(uniq_fn, html_num_states)
  deploy_html.html_add_to_top(uniq_fn, html_su_nm_stats)
  deploy_html.html_add_to_top(uniq_fn, html_version_info)
  
  # get the # of uniq machines and add that to the top of the file as well.
  num_nodes, human_string = deploy_stats.get_uniq_machines('./detailed_logs/controller.'+timestamp)
  deploy_html.html_add_to_top(uniq_fn, human_string)

  
  # total responsive machines = sum up all versions
  sum = 0
  for each_key in node_version_dict.keys():
    # make sure it's not a string key
    if each_key.find('Not') == -1:
      sum += node_version_dict[each_key]
    
  deploy_html.html_add_to_top(uniq_fn, str(sum)+' hosts responded in a timely fashion '+\
      'and ran our tests.')
  
  deploy_html.html_add_to_top(uniq_fn, deploy_stats.insert_timestamp_from_fn(uniq_fn))
  
  return

  
  
if __name__ == "__main__":
  build_summary()
