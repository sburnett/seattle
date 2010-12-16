import os
import shutil

"""
<Purpose>
  Cleans up temporary directories & files created by test_setup.
"""

def main():
  temp_base_installers_dir = os.path.join(os.getcwd(), "dist")
  
  try:
    shutil.rmtree(temp_base_installers_dir)
  except Exception:
    print "\n**********************************************************"
    print "Couldn't clean up temporary directory. Maybe already gone?"
    print "**********************************************************\n"
    raise
    
  
if __name__=="__main__":
  main()