"""
<Program Name>
  update_software.py

<Started>
  December 1, 2008

<Author>
  Carter Butaud

<Purpose>
  Populates the folder that the software updater checks with
  the latest version of the code.
"""

import sys
import make_base_installers

UPDATE_SITE = "/homes/iws/butaud/public_html/updatesite"
DEBUG = False

def update(trunk_location):
  """
  <Purpose>
    Populates the update directory (set by a constant) with the
    program files from the current repository.
  
  <Arguments>
    trunk_location:
      The location of the repository's trunk directory, used to
      find the program files.
    
  <Exceptions>
    IOError on bad filepath.
  
  <Side Effects>
    None.

  <Returns>
    None.
  """
  update_dir = UPDATE_SITE + "/real"
  # If we're in DEBUG mode, don't use the real update
  # directory
  if DEBUG:
    print "Debug mode..."
    update_dir = UPDATE_SITE + "/test"
    make_base_installers.prepare_initial_files(trunk_location, update_dir)

def main():
  global DEBUG
  if len(sys.argv) < 2:
    print "usage: python update_software.py trunk/location/ [-d]"
  else:
    if sys.argv[2] == "-d":
      DEBUG = True
      update(sys.argv[1])
      
if __name__ == "__main__":
  main()
