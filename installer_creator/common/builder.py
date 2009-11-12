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

def _state_key_file_to_publickey_string(key_file_name):
  """
  Read a public key file from the the state keys directory and return it in
  a key string format.
  """
  fullpath = os.path.join(settings.STATE_KEYS_DIR, key_file_name)
  return rsa_publickey_to_string(rsa_file_to_publickey(fullpath))

KEY_GENERATION_BITSIZE = 1024
SEATTLE_OWNER_PUBKEY = "22599311712094481841033180665237806588790054310631222126405381271924089573908627143292516781530652411806621379822579071415593657088637116149593337977245852950266439908269276789889378874571884748852746045643368058107460021117918657542413076791486130091963112612854591789518690856746757312472362332259277422867 12178066700672820207562107598028055819349361776558374610887354870455226150556699526375464863913750313427968362621410763996856543211502978012978982095721782038963923296750730921093699612004441897097001474531375768746287550135361393961995082362503104883364653410631228896653666456463100850609343988203007196015297634940347643303507210312220744678194150286966282701307645064974676316167089003178325518359863344277814551559197474590483044733574329925947570794508677779986459413166439000241765225023677767754555282196241915500996842713511830954353475439209109249856644278745081047029879999022462230957427158692886317487753201883260626152112524674984510719269715422340038620826684431748131325669940064404757120601727362881317222699393408097596981355810257955915922792648825991943804005848347665699744316223963851263851853483335699321871483966176480839293125413057603561724598227617736944260269994111610286827287926594015501020767105358832476708899657514473423153377514660641699383445065369199724043380072146246537039577390659243640710339329506620575034175016766639538091937167987100329247642670588246573895990251211721839517713790413170646177246216366029853604031421932123167115444834908424556992662935981166395451031277981021820123445253"
# The key used as the state key for new donations.
ACCEPTDONATIONS_STATE_PUBKEY = _state_key_file_to_publickey_string("acceptdonation.publickey")

# Path to the customize_installers.py. In this case, it's in the same directory
# as this views.py file.
PATH_TO_CUSTOMIZE_INSTALLER_SCRIPT = os.path.join(os.path.dirname(__file__), 
                                                  "customize_installers.py")


def build_installer(vessel_dict, key_dict, username='', dist_str='wml', vesselinfo=''):
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
        'username' is the generated session ID.
      * If calling from XMLRPC view:
        'username' is the SeattleGENI logged in user's name.
    
    dist_str:
      Which OSes the installers should be built for. (Defaults to all)
    
    vesselinfo:
      Skips the vesselinfo construction out of vessel_dict and key_dict,
      and directly uses the provided vesselinfo. 
      ** Note: Used exclusively by XMLRPC.
    
  <Returns>
    A list of urls pointing to where installers were created.
  """
  
  if username == '':
    raise ValueError("Need to specify username")
  
  if dist_str == '':
    raise ValueError("Invalid dist_str specificiation.")
  
  # TODO: Check dist_str has valid chars
  
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
  if vesselinfo == '':    
    vessel_info_str = _generate_vessel_info(vessel_dict, key_dict)
  else:
    vessel_info_str = vesselinfo

  f = open((temp_installinfo_dir + "/vesselinfo"), 'w')
  f.write(vessel_info_str)
  f.close()

  print("file preparation done. calling customize installer.")
   
  installer_urls_dict = _run_customize_installer(username, dist_str)
  return installer_urls_dict
  
#  try:
#    subprocess.check_call([sys.executable, PATH_TO_CUSTOMIZE_INSTALLER_SCRIPT, dist_str, 
#                           settings.BASE_INSTALLERS_DIR, temp_installinfo_dir, prefix])
#  except subprocess.CalledProcessError:
#    raise 
#  
#  installer_urls_dict = {}
#  if 'w' in dist_str:
#    installer_urls_dict['w'] = settings.USER_INSTALLERS_URL + "%s_dist/seattle_win.zip"%(username)
#  if 'l' in dist_str:
#    installer_urls_dict['l'] = settings.USER_INSTALLERS_URL + "%s_dist/seattle_linux.tgz"%(username)
#  if 'm' in dist_str:
#    installer_urls_dict['m'] = settings.USER_INSTALLERS_URL + "%s_dist/seattle_mac.tgz"%(username)
#  
#  return installer_urls_dict
  


def check_and_build_if_new_installers(installer_id):
  """
  <Purpose>
    Checks if the current user installers exist. If they don't, this function
    will try and rebuild them if it can find the vesselinfo file for the specified
    install. 
    
    Also, checks if the current base installers are newer than the already 
    built installers. If so, rebuild the installers with the newer, more current base 
    installers.
  
  <Returns>
    -1 if base installers are missing or unreadable.
     0 if installers are up to date, and do not require rebuilding.
     1 if installers were rebuilt using newest base installers.
  """
  user_installer_missing = False
  need_rebuild = False
  win_base_mtime = 0
  linux_base_mtime = 0
  mac_base_mtime = 0
  
  try:
    win_stat_buf = os.stat(os.path.join(settings.BASE_INSTALLERS_DIR, "seattle_win.zip"))
    linux_stat_buf = os.stat(os.path.join(settings.BASE_INSTALLERS_DIR, "seattle_linux.tgz"))
    mac_stat_buf = os.stat(os.path.join(settings.BASE_INSTALLERS_DIR, "seattle_mac.tgz"))
  except Exception:
    return -1
  else:
    win_base_mtime = win_stat_buf.st_mtime
    linux_base_mtime = linux_stat_buf.st_mtime
    mac_base_mtime = mac_stat_buf.st_mtime
  
  dist_folder = os.path.join(settings.USER_INSTALLERS_DIR, installer_id + "_dist")
  
  try:
    win_user_stat_buf = os.stat(os.path.join(dist_folder, "seattle_win.zip"))
    linux_user_stat_buf = os.stat(os.path.join(dist_folder, "seattle_linux.tgz"))
    mac_user_stat_buf = os.stat(os.path.join(dist_folder, "seattle_mac.tgz"))
  except Exception:
    user_installer_missing = True
  else:
    win_user_mtime = win_user_stat_buf.st_mtime
    linux_user_mtime = linux_user_stat_buf.st_mtime
    mac_user_mtime = mac_user_stat_buf.st_mtime
    
  # rebuild installers if base installers newer or user installers missing
  if user_installer_missing:
    # rebuild
    need_rebuild = True
  else:  
    if (win_base_mtime > win_user_mtime) or (linux_base_mtime > linux_user_mtime) or (mac_base_mtime > mac_user_mtime):
      need_rebuild = True
  
  if not need_rebuild:
    print "no rebuild needed!"
    return 0
  
  # prepare rebuild, read in existing vesselinfo file
  #  v_handle = open(os.path.join(os.path.join(dist_folder, "install_info"), "vesselinfo"), 'rb')
  #  vesselinfo_data = v_handle.read()
  #  print vesselinfo_data
  #  v_handle.close()
  
  # try to remove existing installers (even though they might not exist, for whatever reason)
  try:
    os.remove(os.path.join(dist_folder, "seattle_win.zip"))
  except Exception:
    print "no win user installer to remove"
    pass
  else:
    print "removed win user installer"
  
  try:
    os.remove(os.path.join(dist_folder, "seattle_linux.tgz"))
  except Exception:
    print "no linux user installer to remove"
    pass
  else:
    print "removed linux user installer"
  
  try:
    os.remove(os.path.join(dist_folder, "seattle_mac.tgz"))
  except Exception:
    print "no mac user installer to remove"
    pass
  else:
    print "removed mac user installer"
  
  print "about to call customize"
  _run_customize_installer(installer_id)
  return 1


  
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
  
  # write in our reserved 20%
  lines.append("Percent 20")
  lines.append("Owner " + SEATTLE_OWNER_PUBKEY)
  
  vessel_info_str = '\n'.join(lines)
  return vessel_info_str



def _run_customize_installer(installer_id, dist_str='wml'):
  prefix = os.path.join(settings.USER_INSTALLERS_DIR, "%s_dist"%(installer_id))
  temp_installinfo_dir = os.path.join(prefix, "install_info")
  
  try:
    subprocess.check_call([sys.executable, PATH_TO_CUSTOMIZE_INSTALLER_SCRIPT, dist_str, 
                           settings.BASE_INSTALLERS_DIR, temp_installinfo_dir, prefix])
  except subprocess.CalledProcessError:
    raise 
  
  installer_urls_dict = {}
  if 'w' in dist_str:
    installer_urls_dict['w'] = settings.USER_INSTALLERS_URL + "%s_dist/seattle_win.zip"%(installer_id)
  if 'l' in dist_str:
    installer_urls_dict['l'] = settings.USER_INSTALLERS_URL + "%s_dist/seattle_linux.tgz"%(installer_id)
  if 'm' in dist_str:
    installer_urls_dict['m'] = settings.USER_INSTALLERS_URL + "%s_dist/seattle_mac.tgz"%(installer_id)
  
  return installer_urls_dict