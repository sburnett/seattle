"""
<Program>
  builder.py

<Author>
  Jason Chen
  jchen@cs.washington.edu

<Started>
  September, 2009
  
<Purpose>
  Contains functions that are related to, or 
  directly involved with the building of the installers.
  
  This code is shared among the HTML and XMLRPC views of the installer_creator.
"""
import os
import sys
import subprocess
import shutil

from installer_creator import settings

from seattle import repyhelper
from seattle import repyportability

repyhelper.translate_and_import("rsa.repy")

KEY_GENERATION_BITSIZE = 1024

# Path to the customize_installers.py. In this case, it's in the same directory
# as this views.py file.
PATH_TO_CUSTOMIZE_INSTALLER_SCRIPT = os.path.join(os.path.dirname(__file__), 
                                                  "customize_installers.py")


def build_installer(vessel_dict, key_dict, username='', dist_str='wlm'):
  """
  <Purpose>
    Creates an installer with the given vessel_dict (vessel definitions)
    and the given key_dict (owner/user key dictionaries)
  
  <Arguments>
    vessel_dict:
      A list of vessel dictionaries, each dict representing a defintion
      of a vessel. Follows the format:
      [ {owner, percentage, [users]}, {owner, percentage, [users]} ... ]
    
    key_dict:
      A dictionary whose keys are usernames, and whose 
      values are key dicts (pubkey & privkey). Follows the format:
      { 'user1' : {'pubkey':pubkey, 'privkey':privkey}, 'user2' ... } 
  
    username:
      * If calling from HTML view:
        'username' is the django session id.
      * If calling from XMLRPC view:
        'username' is the SeattleGENI logged in user's name.
    
    dist_str:
      Which OSes the installers should be built for. (Defaults to all)
    
  <Returns>
    A list of urls pointing to where installers were created.
  """
  
  if username == '':
    raise ValueError("Need to specify username")
  
  if dist_str == '' or dist_str not in 'wlm':
    raise ValueError("Invalid dist_str specificiation.")
  
  prefix = os.path.join(settings.USER_INSTALLERS_DIR, "%s_dist"%(username))
  temp_installinfo_dir = os.path.join(prefix, "install_info")
  
  # remove and recreate the prefix dir
  shutil.rmtree(prefix, True)

  # create install dir
  os.mkdir(prefix)
 
  # create the install_info dir, a temporary directory where the vesselinfo
  # will reside right before it gets added into the install package by installer_creator
  os.mkdir(temp_installinfo_dir)

  # prepare & write out the vesselinfo file
  vessel_info_str = _generate_vessel_info(vessel_dict, key_dict)

  f = open((temp_installinfo_dir + "/vesselinfo"), 'w')
  f.write(vessel_info_str)
  f.close()

  print("file preparation done. calling customize installer.")
  
  
#  try:
#    subprocess.check_call([sys.executable, PATH_TO_CUSTOMIZE_INSTALLER_SCRIPT, dist_str, 
#                           settings.BASE_INSTALLERS_DIR, temp_installinfo_dir, prefix])
#  except subprocess.CalledProcessError:
#    raise 
  
  installer_urls_dict = {}
  if 'w' in dist_str:
    installer_urls_dict['w'] = settings.USER_INSTALLERS_URL + "%s_dist/seattle_win.zip"%(username)
  if 'l' in dist_str:
    installer_urls_dict['l'] = settings.USER_INSTALLERS_URL + "%s_dist/seattle_linux.tgz"%(username)
  if 'm' in dist_str:
    installer_urls_dict['m'] = settings.USER_INSTALLERS_URL + "%s_dist/seattle_mac.tgz"%(username)
  
  return installer_urls_dict
  
  

def generate_keypair():
  (pubkeydict, privkeydict) = rsa_gen_pubpriv_keys(KEY_GENERATION_BITSIZE)

  pubkeystring = rsa_publickey_to_string(pubkeydict)
  privkeystring = rsa_privatekey_to_string(privkeydict)
  
  return {'pubkey' : pubkeystring, 'privkey' : privkeystring}



def _generate_vessel_info(vessel_dict, key_dict):
  lines = []
  for vessel in vessel_dict:
    percentage = str(vessel['percentage'] * 10)
    owner_keypair = key_dict[vessel['owner']] 
    owner_pubkey = owner_keypair['pubkey']
    
    lines.append("Percent " + percentage)
    lines.append("Owner " + owner_pubkey)
    for user in vessel['users']:
      user_keypair = key_dict[user]
      user_pubkey = user_keypair['pubkey']
      lines.append("User " + user_pubkey)
    
  vessel_info_str = '\n'.join(lines)
  return vessel_info_str



