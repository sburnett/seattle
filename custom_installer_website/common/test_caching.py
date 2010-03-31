import os

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

def main():
  
  print "*** BEGIN custom installer service CACHE TESTING ***"
  # override builder's _send_file method so we don't actually try to serve up the installers
  builder._send_file = lambda self: 0
  
  temp_base_installers_dir = os.path.join(os.getcwd(), "dist")
  temp_user_installers_dir = os.path.join(temp_base_installers_dir, "geni")

  # override settings file so installer directory is set to temporary local
  settings.BASE_INSTALLERS_DIR = temp_base_installers_dir
  settings.USER_INSTALLERS_DIR = temp_user_installers_dir

  vessel_list = [{'owner':'jchen', 'percentage':40, 'users':[]}, {'owner':'jchen_two', 'percentage':40, 'users':[]}]
  pubkey_dict = {'jchen': {'pubkey':'jchen_pubkey1234'}, 'jchen_two':{'pubkey':'jchen_two_pubkey1234'}}
  
  print "*** Preparing directory/vesselinfo for installer build... ",
  ret = views.PublicXMLRPCFunctions.create_installer(vessel_list, pubkey_dict, "windows")
  print "OK"
  
  build_id = ret.split("/")[5]
  installer_name = "seattle_win.zip"
  inst_build_dir = os.path.join(temp_user_installers_dir, build_id)
  
  print "*** Removing any previous installers from previous test runs... ",
  try:
    os.remove(os.path.join(inst_build_dir, "seattle_win.zip"))
    os.remove(os.path.join(inst_build_dir, "seattle_mac.tgz"))
    os.remove(os.path.join(inst_build_dir, "seattle_linux.tgz"))
  except Exception:
    pass
  
  print "OK"
  
  print "*** Simulating installer download request                   "
  print "*** [initial request, expect a fresh installer to be built] "
  print builder.dl_installer({}, build_id, installer_name)
  
  
  

if __name__=="__main__":
  main()