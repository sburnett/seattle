import os

from custom_installer_website.common import builder
from custom_installer_website.xmlrpc import views
from custom_installer_website import settings

"""
<Purpose>
  Tests the custom installer's locking mechanisms by creating installers and having
  the custom installer hold a significantly long lock, giving other instances of this
  test to try and create the same installer instance.

<Usage>
  * Run test_setup.py first, to setup isolated temporary directory.
  
  This test is designed to have multiple copies of itself running.
  Run one instance, and once the lock is obtained, run another instance of the test.
  (The custom installer's lock time will be increased for this test)
  
  The goal is to see whether the second instance hangs and waits for the first instance
  to release its write lock (indicating correct operation).  
"""

ACTUALLY_BUILD_INSTALLERS = False

def main():
  # override builder's LOCK_RELEASE_DELAY to something long (10 sec)
  builder.LOCK_RELEASE_DELAY = 10
  
  # override builder's _send_file method so we don't actually try to serve up the installers
  builder._send_file = lambda self: 0
  
  temp_base_installers_dir = os.path.join(os.getcwd(), "dist")
  temp_user_installers_dir = os.path.join(temp_base_installers_dir, "geni")

  # override settings file so installer directory is set to temporary local
  settings.BASE_INSTALLERS_DIR = temp_base_installers_dir
  settings.USER_INSTALLERS_DIR = temp_user_installers_dir
  
  if ACTUALLY_BUILD_INSTALLERS == False:
    builder._run_customize_installer = lambda self: 0
  
  # override builder's test flag so dl_installer returns us the cache check return value rather than sending us a file
  builder.TEST_RETURN_CHECK_RET = True
  
  vessel_list = [{'owner':'jchen', 'percentage':40, 'users':[]}, {'owner':'jchen_two', 'percentage':40, 'users':[]}]
  pubkey_dict = {'jchen': {'pubkey':'jchen_pubkey1234'}, 'jchen_two':{'pubkey':'jchen_two_pubkey1234'}}
  
  # prepare installer creation filesystem environment
  print "*** Preparing directory/vesselinfo for installer build..."
  ret = views.PublicXMLRPCFunctions.create_installer(vessel_list, pubkey_dict, "windows")

  print ""
  print "*** Simulating installer download request..."
  build_id = ret.split("/")[4]
  installer_name = "seattle_win.zip"
  
  builder.dl_installer({}, build_id, installer_name)


if __name__=="__main__":
  main()