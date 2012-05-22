"""
<Program Name>
  prepare_seattlegeni_server.py

<Purpose>
  To set up the seattlegeni xmlrpc server partway.
  This program copies/creates/modifies some files that
  are necessary to run the server. This file should be run
  from the folder that was extracted from the tarball so all
  the other files that were provided should be in the same
  directory.

<Usage>
  python prepare_seattlegeni_server.py target_folder_path
"""

import sys
import os
import shutil
import urllib


TARGET_DIR = ""
CURRENT_DIR = ""

create_required_files_list = ['seattleclearinghouse_xmlrpc.logfile', 'protogeni_user_file.txt',
                              'protogeni_vessel_handle.txt', '__lockfile__']

def main():
  """
  <Purpose>
    Copies the necessary files over to the target folder.
    Creates the necessary files needed by the server.
    Changes the mode of the file so its accessible by the
    server.

  <Side Effects>
    Files are created.
    Some files are downloaded.   
  
  <Exceptions>
    None

  <Return>
    None
  """

  if len(sys.argv) < 2:
    print "Target folder not provided."
    print "Usage:\n  $> python prepare_seattlegeni_server.py target_folder_path"
    exit(1)

  
  # Fill in the directory paths.
  CURRENT_DIR = os.getcwd()
  TARGET_DIR = os.path.abspath(sys.argv[1])

  file_list = os.listdir(CURRENT_DIR)

  omit_directory = False

  print "\nPreparing to copy necessary files to "+TARGET_DIR

  # Copy all the necessary files over.
  for current_file in file_list:
    if os.path.isfile(current_file):
      print "Copying file....."+current_file
      shutil.copy(os.path.join(CURRENT_DIR, current_file), TARGET_DIR)
    elif os.path.isdir(current_file):
      if os.path.isdir(os.path.join(TARGET_DIR, current_file)):
        print "Omitted copying directory....."+current_file
        omit_directory = True
      else:
        print "Copying directory....."+current_file
        shutil.copytree(os.path.join(CURRENT_DIR, current_file), 
          os.path.join(TARGET_DIR, current_file))
 
  if omit_directory:    
    print "If any directory was omitted, then make sure that the directory doesn't exist in target folder."

  
  print "\nPreparing to create files needed by the XMLRPC server to "+TARGET_DIR

  # Create the required files.
  for current_file in create_required_files_list:
    print "Creating file....."+current_file
    file_path = os.path.join(TARGET_DIR, current_file)
    file = open(file_path, 'w')
    file.write('')
    file.close()

  print "\nDownloading required files to "+TARGET_DIR

  # Download the genica.bundle and genicrl.bundle
  for file in ["genica.bundle", "genicrl.bundle"]:
    print "Downloading file....."+file
    urllib.urlretrieve("https://www.emulab.net/"+file, os.path.join(TARGET_DIR, file))
  
  
  print "Changing mode of files in directory: " + TARGET_DIR
  # Change the mode of all the files
  os.system("chmod 777 "+TARGET_DIR+"/*")

  print """
##################################################################################
#  All the necessary files for the XMLRPC server to run has been copied          
#  over and downloaded to the folder: """ + TARGET_DIR +"""                      
#                                                                                
#  In order to finish the setup please edit the files listed below and            
#  set the appropriate variable values as listed below.            
#
#  Before modifying the files, the protogeni Reference Component Manager files 
#  and Seattle library files should already be downloaded to some folder. This             
#  should have been done in Step 2 and 3 in the README.txt             
#                                                                 
#  seattleclearinghouse_xmlrpc_server.pl:                                                  
#    * use lib '/path/to/protogeni/reference-cm-2.0/xmlrpc'; (Line 12)
#    * use lib '/path/to/protogeni/reference-cm-2.0/lib'; (Line 13)   
#    * $directory_prefix = '""" + TARGET_DIR + """'; (Line 36)                    
#    * $server_url = 'https://seattlegeni.cs.washington.edu/xmlrpc/'; (Line 40)   
#                                                                                
#  generate_pubkey.py:                                                           
#    * sys.path.append("where/the/seattle/library/files/are/located) (Line 2)    
#
#  protogeni_user_file.txt:
#    * Add all the seatlegeni users that have been allocated for this server.
#      Each of the line in this file should follow the format:
#  
#        seattlegeni_username:password_for_user:1:0:0
#     
#      The last 3 values are set by default to 1:0:0 but this will get changed
#      to some other value after the XMLRPC server has run.
#
# Please contact Monzur Muhammad (monzum@cs.washington.edu) with any questions! 
##################################################################################
"""

  



  
if __name__ == "__main__":
  main()
