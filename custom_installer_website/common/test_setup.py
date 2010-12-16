import os
import shutil
import sys

from custom_installer_website import settings

"""
<Purpose>
  This will create a temporary installer directory in the current directory,
  and also COPIES over the installers from the "real" BASE_INSTALLERS_DIR.

  This results in tests being able to run isolated from the production installer directory. 
  Remember to run test_teardown when done testing to cleanup temporary dirs.
"""

def main():   

  temp_base_installers_dir = os.path.join(os.getcwd(), "dist")
  temp_user_installers_dir = os.path.join(temp_base_installers_dir, "geni")
  
  try:
    os.mkdir(temp_base_installers_dir)
    os.mkdir(temp_user_installers_dir)
    shutil.copy(os.path.join(settings.BASE_INSTALLERS_DIR, "seattle_win.zip"), temp_base_installers_dir)
    shutil.copy(os.path.join(settings.BASE_INSTALLERS_DIR, "seattle_mac.tgz"), temp_base_installers_dir)
    shutil.copy(os.path.join(settings.BASE_INSTALLERS_DIR, "seattle_linux.tgz"), temp_base_installers_dir)
  except Exception:
    raise
    sys.exit("Couldn't create local temporary directories or failed to copy installers.\nPlease run test_teardown and run test setup again.") 
    
if __name__=="__main__":
  main()