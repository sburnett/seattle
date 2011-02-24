"""
<Program Name>
  build_manager.py

<Started>
  September 2010

<Author>
  Alex Hanson

<Purpose>
  Provides BuildManager class that orchestrates the process of interpreting
  user input and building a custom installer.
"""


import hashlib
import os
import random
import shutil
import tempfile

from django.conf import settings
from django.core.urlresolvers import reverse

import custominstallerbuilder.common.constants as constants
import custominstallerbuilder.common.packager as packager
import custominstallerbuilder.common.validations as validations


# Import Repy module to generate cryptographic keys. This requires that the
# Seattle standard library is within the Python path.
import repyhelper
repyhelper.translate_and_import('rsa.repy')


class BuildManager:
  """
  <Purpose>
    Performs validation of build data and helps automate the task of
    building custom installers.
  
  <Side Effects>
    Several operations touch the disk in order create (or prepare to create)
    the custom installers.
  
  <Example Use>
    vessels = [{'percentage': 80, 'owner': 'alex', 'users': ['bill']}]
    
    user_data = {
      'alex': {'public_key': alex_public_key},
      'bill': {'public_key': bill_public_key},
    }
    
    manager = BuildManager(vessels, user_data)
    return manager.build()
  
  <Note>
    The "add_*", "set_*", and "clear_*" functions do exactly what their name
    implies. Rigorous documentation for these functions has been omitted.
  """

  
  #################
  ## Basic setup ##
  #################

  
  def __init__(self, vessel_list=None, user_data=None, build_id=None):
    # Start with clean values.
    self.clear()
    
    # Populate the object with any provided build data. In most cases, none of
    # following arguments will be specified if a build ID was given.
    if vessel_list:
      self.set_vessels(vessel_list)
    
    if user_data:
      self.set_users(user_data)
    
    # To work with previously prepared installers, a build ID may be specified.
    if build_id:
      self.set_build_id(build_id)




  
  def clear(self):
    self.clear_vessels()
    self.clear_users()
    self.clear_build_id()





  
  ##############
  ## Building ##
  ##############

  
  def clear_build_id(self):
    self.build_id = None



  def set_build_id(self, build_id):
    validations.validate_build_id(build_id)
    self.build_id = build_id


  
  def get_build_directory(self):
    return os.path.abspath(os.path.join(settings.CUSTOM_INSTALLER_ROOT, self.build_id))





  def get_urls(self):
    """
    <Purpose>
      Returns the URLs where installer packages for the given build ID can be
      found. If installers are requested with these URLs, they will be
      automatically generated, assuming the build ID is valid.
    
    <Arguments>
      None.
    
    <Exceptions>
      None.
    
    <Side Effects>
      None.
    
    <Returns>
      A dictionary which contains the requested URLs to the given platform packages.
    """
    
    url_strings = dict()
    
    
    for platform in constants.PLATFORMS:
      download_path = reverse('download-installer', kwargs={
        'build_id': self.build_id,
        'platform': platform,
      })
      
      url_strings[platform] = settings.BASE_URL.rstrip('/') + download_path
    
    
    return url_strings
    
    
    
    
  def get_static_urls(self): 
    """
    <Purpose>
      Returns the URLs where installer packages for the given build ID can be
      found, assuming they have already been built. These URLs will not be
      automatically generated, so these URLs should only be used internally.
    
    <Arguments>
      None.
    
    <Exceptions>
      None.
    
    <Side Effects>
      None.
    
    <Returns>
      A dictionary which contains the requested URLs to the given platform packages.
    """
    
       
    url_strings = dict()
    
    
    for platform in constants.PLATFORMS:
      if self.installer_exists(platform):
        download_url = (settings.CUSTOM_INSTALLER_URL.rstrip('/') + '/' +
                        self.build_id + '/' + constants.PLATFORM_BUNDLES[platform])
      else:
        download_url = None
      
      url_strings[platform] = download_url
    
    
    return url_strings





  def _compile_vessel_info(self):
    vessel_info = []

    # Create an entry for each user-defined vessel.
    for vessel in self.vessel_list:
      percentage = str(vessel['percentage'])
      owner_public_key = self.users[vessel['owner']]['public_key']

      vessel_info.append('Percent ' + percentage)
      vessel_info.append('Owner ' + owner_public_key)

      for user in vessel['users']:
        user_public_key = self.users[user]['public_key']
        vessel_info.append('User ' + user_public_key)


    # Create a vessel for the reserved resources.
    vessel_info.append('Percent ' + str(settings.RESERVED_PERCENTAGE))
    vessel_info.append('Owner ' + settings.RESERVED_PUBLIC_KEY)

    # Pack all the vessel information into one string, fit for writing to a
    # vesselinfo file.
    vessel_info = '\n'.join(vessel_info)
    return vessel_info





  def installer_exists(self, platform):
    """
    <Purpose>
      Checks if the given installer already exists. Returns True if it does,
      False otherwise.
    
    <Arguments>
      platform:
        A string representing the installer to check. For example, "linux".
    
    <Exceptions>
      None.
    
    <Side Effects>
      None.
    
    <Returns>
      A boolean value.
    """
    
    validations.validate_platform(platform)
    
    installer_filename = os.path.join(
      settings.CUSTOM_INSTALLER_ROOT,
      self.build_id,
      constants.PLATFORM_BUNDLES[platform]
    )

    if os.path.isfile(installer_filename):
      return True
      
    return False



  def prepare(self):
    """
    <Purpose>
      Constructs the vesselinfo file that can later be used to package
      installer archives. Also returns build data (including cryptographic
      keys) that may be helpful to the user.
    
    <Arguments>
      None.
    
    <Exceptions>
      None.
    
    <Side Effects>
      The vesselinfo file will be written to the disk.
    
    <Returns>
      Data related to the build.
    """
    

    # Perform a little clean-up.
    validations.validate_percentage_total(self.vessel_percentage_total())
    self._generate_missing_keys()
    
    # Establish this variable to use within the following loop.
    build_dir = None
  
    # Create a random build ID. Retry if there was a collision.
    while True:
      self.build_id = hashlib.sha1(str(random.random())).hexdigest()
      build_dir = self.get_build_directory()
      
      if not os.path.exists(build_dir):
        break 
  
    # Get the name of our build directory, and select a temporary directory to
    # perform our work in.
    build_dir = self.get_build_directory()
    temp_dir = tempfile.mkdtemp()
    
    # Write the vesselinfo file into the temporary directory.
    vessel_info = self._compile_vessel_info()
    vessel_info_filename = packager.write_vessel_info(vessel_info, temp_dir)
    
    # Create the destination directory if it does not exist.
    if not os.path.isdir(build_dir):
      os.makedirs(build_dir, constants.DIR_PERMISSIONS)
      
    # Move the vesselinfo file into that destination directory.
    destination_filename = os.path.abspath(os.path.join(build_dir, os.path.split(vessel_info_filename)[1]))
    shutil.move(vessel_info_filename, destination_filename)

    # Remove the temporary directory.
    shutil.rmtree(temp_dir)
    
    # Return information about the build.
    return_dict = {
      'installers': self.get_urls(),
      'users': self.users,
      'build_id': self.build_id,
    }
    
    return return_dict





  def package(self, platform):
    """
    <Purpose>
      Constructs an installer for the given platform, assuming a vesselinfo
      file already exists. 
    
    <Arguments>
      None.
    
    <Exceptions>
      ValidationError if the vesselinfo file does not already exist.
    
    <Side Effects>
      The installer will be written to disk.
    
    <Returns>
      Nothing.
    """
    
    # Validate the platform.
    validations.validate_platform(platform)
    
    # Get the name of our build directory, and select a temporary directory to
    # perform our work in.
    build_dir = self.get_build_directory()
    temp_dir = tempfile.mkdtemp()
    
    
    # Copy the existing vesselinfo file into place.
    source_vesselinfo_fn = os.path.join(build_dir, 'vesselinfo')
    destination_vesselinfo_fn = os.path.join(temp_dir, 'vesselinfo')
    
    if not os.path.isfile(source_vesselinfo_fn):
      raise validations.ValidationError('There is no vesselinfo file for the given build ID.')
    
    shutil.copy(source_vesselinfo_fn, destination_vesselinfo_fn)
    
    
    # Create packages for the requested installers.
    packager.package_installers(temp_dir, [platform])
      
    # Move each file in the temporary directory to the destination directory.
    for file_to_move in os.listdir(temp_dir):
      source_filename = os.path.abspath(os.path.join(temp_dir, file_to_move))
      destination_filename = os.path.abspath(os.path.join(build_dir, file_to_move))
      shutil.move(source_filename, destination_filename)

    # Remove the temporary directory.
    shutil.rmtree(temp_dir)





  #############
  ## Vessels ##
  #############
 
  
  def clear_vessels(self):
    self.vessel_list = list()



 
  
  def add_vessel(self, percentage, owner, user_list=None):
    validations.validate_percentage(percentage)
    
    if owner is None:
      raise validations.ValidationError('All vessels must have a specified owner.')
    else:
      self.add_user(owner, override=False)
    
    if user_list:
      user_set = set(user_list)
      
      for user in user_set:
        self.add_user(user, override=False)
    else:
      user_set = set()
    
    self.vessel_list.append({
      'percentage': percentage,
      'owner': owner,
      'users': user_set,
    })





  
  def set_vessels(self, vessels):
    self.clear_vessels()
    for vessel in vessels:
      self.add_vessel(vessel['percentage'], vessel.get('owner', None), vessel.get('users', None))




    
  
  def vessel_percentage_total(self):
    total_percentage = 0
    for vessel in self.vessel_list:
      total_percentage += vessel['percentage']
    return total_percentage




  
  ###########
  ## Users ##
  ###########

  
  def clear_users(self):
    self.users = dict()





  def add_user(self, name, public_key=None, override=True):
    if (name in self.users) and (not override):
      return
    
    validations.validate_username(name)
    
    if public_key:
      validations.validate_public_key(public_key)
    
    self.users[name] = {'public_key': public_key}




  
  def set_users(self, user_data):
    for name in user_data:
      self.add_user(name, user_data[name].get('public_key', None))





  def _generate_missing_keys(self):
    for user_name in self.users:
      if self.users[user_name].get('public_key', None) is not None:
        continue
      
      (public_key_dict, private_key_dict) = rsa_gen_pubpriv_keys(settings.RSA_BIT_LENGTH)
      
      self.users[user_name]['public_key'] = rsa_publickey_to_string(public_key_dict)
      self.users[user_name]['private_key'] = rsa_privatekey_to_string(private_key_dict)
