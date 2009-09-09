"""
<Program Name>
  log_maintenance.py

<Started>
  Aug 2009

<Author>
  n2k8000@u.washington.edu
  Konstantin Pik

<Purpose>
  Script provides methods that'll summarize all files in a directory.

<Usage>
  Script is used to run manually on files that have not been summarized.
  
"""

import deploy_html
import deploy_helper
import os
import sys

# this file will crawl log directories and import the latest summary tools


def summarize_file(file_path):
  """
  <Purpose>
    Summarizes a file given a file path, and writes it back to the same file.

  <Arguments>
    file_path:
      The path to the file relative to this file where the file you
      want to be summarized resides.

  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    None.
  """
  
  try:
    # read in the whole file
    file_handle = open(file_path, 'r')
    file_content = deploy_html.read_whole_file(file_handle)
    file_handle.close()
    
    # grab the contents
    final_content = deploy_helper.summarize_all_blocks(file_content)
    
    # write the file contents again only if it changed.
    if final_content != file_content:
      # remake the file.
      file_handle = open(file_path, 'w+')
      file_handle.write(final_content)
      file_handle.close()
    
    print "Summarized "+file_path
  except Exception, e:
    print e



def summarize_dir(directory):
  """
  <Purpose>
    Summarizes all the files in a directory, and all files within that directory.
    
  <Arguments>
    directory:
      the directory to summarize ( and all child directories as well)

  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    None.
  """
  
  if os.path.isdir(directory):
    for each_dir in os.listdir(directory):
      if os.path.isdir(directory+'/'+each_dir):
        # it's a directory! now summarize each file
        for each_file in os.listdir(directory+'/'+each_dir):
          if os.path.isfile(directory+'/'+each_dir+'/'+each_file):
            # summarize the file!
            summarize_file(directory+'/'+each_dir+'/'+each_file)



def main():
  # entry point into the program.  If there is an argument
  # then we clean out deploy.logs, and if there isn't an argument
  # then we clean out the detailed_logs directory.
  if len(sys.argv) == 2:
    # clean up deploy_logs directory
    summarize_dir('deploy.logs')
  else:
    summarize_dir('detailed_logs')
    

if __name__ == '__main__':
  main()
