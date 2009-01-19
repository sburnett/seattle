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

import preparetest

def main():
  # this is for preparetest to work
  current_dir = os.getcwd()
  os.chdir(current_dir + "/../")
  preparetest.main()

  target_dir = sys.argv[1]
  
  # set working directory back to the folder we've started in
  os.chdir(current_dir)

  # copy files to target dir
  preparetest.copy_to_target("node_state_transitions/*", target_dir)

  # set working dir to target
  os.chdir(target_dir)
  
  # call the process_mix function to process all mix files in the target directory
  preparetest.process_mix("repypp.py")

  # go back to root project directory
  os.chdir(current_dir) 

if __name__ == '__main__':
  main()
