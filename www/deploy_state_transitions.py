"""
<Program Name>
  deploy_state_transitions.py

<Started>
  January 19, 2008

<Author>
  ivan@cs.washington.edu
  Ivan Beschastnikh

<Purpose>
  Deploys the state transition scripts along with all the necessary
  repy libs into a single directory. Uses preparetest.py internally
  and has similar behavior.

<Description>
  The script first erases all the files in the target folder, then
  copies the necessary test files to it. Afterwards, the .mix files in
  the target folder are run through the preprocessor.  It is required
  that the folder passed in as an argument to the script exists.

<Usage>
  PYTHONPATH=$PYTHONPATH:/home/geni/trunk/ && deploy_state_transitions.py <target_folder>
  
"""

import os
import sys
import setup_crontab
import glob

try:
  import preparetest
except ImportError:
  print "Error importing preparetest, make sure that preparetest is in your PYTHONPATH"
  sys.exit(0)

def main():

  checkArgs()

  #setup some variables for cron setup
  cron_setup = False
  log_dir = ""

  # -c means we have to setup the crontab with a new cron job
  if sys.argv[1] == '-c':
    cron_setup = True
    sys.argv = sys.argv[1:]
    checkArgs(cron_setup)
    log_dir = sys.argv[2]
    
    if not( os.path.isdir(log_dir) ):
      help_exit("given log_foldername is not a directory")
	  
  #set up all the variables about directory information
  current_dir = os.getcwd()
  
  #ensures that the backslashes and forward slashes are proper for the OS
  target_dir = os.path.normpath(sys.argv[1])

  #make sure svn is up to date and start up preparetest
  os.chdir(os.path.normpath(current_dir + "/../trunk"))
  os.system("svn up")
  os.chdir(current_dir)
  preparetest.main()

  if not( os.path.isdir(target_dir) ):
    help_exit("given foldername is not a directory")

  #change to target directory and clean up the target directory folder
  os.chdir(target_dir)

  files_to_remove = glob.glob("*")

  for f in files_to_remove:
    if os.path.isdir(f):
      shutil.rmtree(f)
    else:
      os.remove(f)

  os.chdir(current_dir)

  #the next few lines is necessary unless the file is manually copied over
  preparetest.copy_to_target("../trunk/www/node_state_transitions/*", target_dir)
  
  # set working dir to target
  os.chdir(target_dir)
  
  # call the process_mix function to process all mix files in the target directory
  preparetest.process_mix(current_dir+"/repypp.py")

  #check to see if cron setup was requested, if yes run cron_setup
  if cron_setup:

    #create the absolute path for the log file and the file needed for the 
    #cron job
    cron_tab_dir=os.path.normpath(current_dir + "/" + target_dir)
    cron_log_dir=os.path.normpath(current_dir + "/" + log_dir)
    
    cron_line="@reboot /usr/bin/python " + cron_tab_dir + "/donationtocanonical.py >> " + cron_log_dir + "/cron_log.donationtocanonical 2>&1" + os.linesep

    #setup the cron job
    setup_crontab.add_crontab(cron_line, "donationtocanonical")
	
    cron_line="@reboot /usr/bin/python " + cron_tab_dir + "/canonicaltoonepercent_manyevents.py >> " + cron_log_dir + "/cron_log.canonicaltoonepercent_manyevents 2>&1" + os.linesep

    #setup the cron job
    setup_crontab.add_crontab(cron_line, "canonicaltoonepercent_manyevents")
	
    cron_line="@reboot /usr/bin/python " + cron_tab_dir + "/onepercenttoonepercent_manyevents.py >> " + cron_log_dir + "/cron_log.onepercenttoonepercent_manyevents 2>&1" + os.linesep

    #setup the cron job
    setup_crontab.add_crontab(cron_line, "onepercenttoonepercent_manyevents")
	
    cron_line="@reboot /usr/bin/python " + cron_tab_dir + "/expire_vessels.py >> " + cron_log_dir + "/cron_log.expire_vessels 2>&1" + os.linesep

    #setup the cron job
    setup_crontab.add_crontab(cron_line, "expire_vessels")



 
#checks to make sure that the right amount of arguments are provided 
def checkArgs(cron=False):

  if cron and len(sys.argv) < 3:
    help_exit("Invalid number of arguments with option -c, need <log_directory>")
    
  elif len(sys.argv) < 2:
    help_exit("Invalid number of arguments")
   
  

#exit program with a message and help menu
def help_exit(exit_msg):
  print exit_msg
  option_message = "Options:\n -c\tsetup crontab"
  print "python deploy_state_transitions.py [option] <target_directory> [<log_directory>]"
  print option_message
  sys.exit(1)
  
if __name__ == '__main__':
  main()
