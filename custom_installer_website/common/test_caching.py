import os
import sys

from custom_installer_website.common import builder
from custom_installer_website.xmlrpc import views
from custom_installer_website import settings

"""
<Purpose>
  Tests the custom installer's caching system by simulating different base installer and
  user installer combinations, and checks to see whether the custom installer correctly
  caches or regenerates installers.
  
<Usage>
  * Run test_setup.py first, to setup isolated temporary directory.
"""

ACTUALLY_BUILD_INSTALLERS = True

def main():
  
  print "*** BEGIN custom installer service CACHE TESTING ***"
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
  
  print "*** Preparing directory/vesselinfo for installer build... ",
  ret = views.PublicXMLRPCFunctions.create_installer(vessel_list, pubkey_dict, "windows")
  
  build_id = ret.split("/")[4]
  installer_name = "seattle_win.zip"
  inst_build_dir = os.path.join(temp_user_installers_dir, build_id)
  
  print "*** Removing any previous installers from previous test runs... ",
  try:
    os.remove(os.path.join(inst_build_dir, "seattle_win.zip"))
    os.remove(os.path.join(inst_build_dir, "seattle_mac.tgz"))
    os.remove(os.path.join(inst_build_dir, "seattle_linux.tgz"))
  except Exception:
    pass
  
  """
    builder's cache check (check_if_need_new_installers) function returns:
    -1 if base installers are missing or unreadable.
     0 if installers are up to date, and do not require rebuilding.
     1 if installers should be rebuilt using newest base installers.
  """
  
  print "*** Simulating installer download request                 "
  print "*** [initial request, expect user installers to be built] "
  cache_check_ret = builder.dl_installer({}, build_id, installer_name)
  
  # we expect installers should be rebuilt (1)
  if cache_check_ret != 1:
    sys.exit("!!! FAILURE. Expected installers to be rebuilt (1), got " + str(cache_check_ret))
  
  print "*** Simulating installer download request                "
  print "*** [user installers up to date, expect cached response] "
  cache_check_ret = builder.dl_installer({}, build_id, installer_name)
  
  # we expect installers should be up to date (0)
  if cache_check_ret != 0:
    sys.exit("!!! FAILURE. Expected installers to be up-to-date & cached response (0), got " + str(cache_check_ret))
  
  # touch base installers, to force a rebuild
  os.utime(os.path.join(temp_base_installers_dir, "seattle_win.zip"), None)

  print "*** Simulating installer download request                                "
  print "*** [base installers just updated, expect user installers to be rebuilt] "
  cache_check_ret = builder.dl_installer({}, build_id, installer_name)
  
  # we expect installers should be up to date (1)
  if cache_check_ret != 1:
    sys.exit("!!! FAILURE. Expected installers to be rebuilt (1), got " + str(cache_check_ret))

  print ""
  print "*** ALL TESTS PASSED ***"

if __name__=="__main__":
  main()