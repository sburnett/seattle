"""
<Program Name>
  packager.py

<Started>
  September 2010

<Author>
  Alex Hanson

<Purpose>
  Packages the finalized custom installers and cryptographic key archives.
  Also provides useful constants toward these ends.
  
  This file expects a Unix-like environment with gzip, tar, and zip commands.
"""

import os
import shutil
import subprocess
import tempfile

from django.conf import settings

import custominstallerbuilder.common.constants as constants



###############
## Functions ##
###############

def write_vessel_info(vessel_info, dir_name):
  """
  <Purpose>
    Takes the given vessel_info and writes it to right place in the given build
    directory.

  <Arguments>
    vessel_info:
      A string of the contents of the vessel_info file to be written.
      
    dir_name:
      The root build directory in which to place the vesselinfo file.

  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    None.
  """
  
  vessel_info_filename = os.path.join(dir_name, 'vesselinfo')
  vessel_info_fileobj = open(vessel_info_filename, 'w')
  vessel_info_fileobj.write(vessel_info)
  vessel_info_fileobj.close()
  
  os.chmod(vessel_info_filename, constants.FILE_PERMISSIONS)
  
  return vessel_info_filename





def package_installers(working_dir, build_platforms):
  """
  <Purpose>
    References the files in the given build directory to build the finalized
    custom installers for the given build platforms.

  <Arguments>
    working_dir:
      The directory in which the installer configuration files are held, and
      where the finalized installer will be placed. Should be an absolute path.
      
    build_platforms:
      A list of the platforms for which installers should be packaged.

  <Exceptions>
    None.

  <Side Effects>
    Creates the installer archives in the given build directory.

  <Returns>
    None.
  """
      
  # The directory which holds the files to be added to the bundles, specified
  # both relative to the working directory and with an absolute path.
  config_dir_rel = os.path.join('.', constants.TEMP_DIR_NAMES['config'])
  config_dir_abs = os.path.join(working_dir, constants.TEMP_DIR_NAMES['config'])
  
  # Create that directory if it doesn't exist already.
  if not os.path.isdir(config_dir_abs):
    os.makedirs(config_dir_abs, constants.DIR_PERMISSIONS)
  
  # Copy the vesselinfo file into place.
  shutil.copy(os.path.join(working_dir, 'vesselinfo'), os.path.join(config_dir_abs, 'vesselinfo'))  
  
        
  base_installers = dict()
    
  for platform in build_platforms:
    base_installer = os.path.abspath(os.path.join(settings.BASE_INSTALLER_ROOT,
                                                  constants.PLATFORM_BUNDLES[platform]))
    
    shutil.copy(base_installer, working_dir)
    base_installer = os.path.join(working_dir, constants.PLATFORM_BUNDLES[platform])
    
    os.chmod(base_installer, constants.FILE_PERMISSIONS)
    
    base_installers[platform] = base_installer
  
  for platform in (constants.ZIP_PLATFORMS & set(build_platforms)):
    subprocess.call(['zip', '-r', base_installers[platform], config_dir_rel], cwd=working_dir)
    
  for platform in (constants.TGZ_PLATFORMS & set(build_platforms)):
    orig = base_installers[platform]
    temp = base_installers[platform] + '.tmp'
    
    subprocess.call(['gzip', '-c', '-d', orig], cwd=working_dir, stdout=open(temp, 'wb'))
    subprocess.call(['tar', '-rf', temp, config_dir_rel], cwd=working_dir)
    subprocess.call(['gzip', '-c', temp], cwd=working_dir, stdout=open(orig, 'wb'))
    
    os.remove(temp)
    os.chmod(orig, constants.FILE_PERMISSIONS)

  for platform in (constants.APK_PLATFORMS & set(build_platforms)):
    orig = base_installers[platform]
    align = base_installers[platform] + '.align'

    # Modify seattle.zip
    subprocess.call(['unzip', orig, 'res/raw/seattle.zip'], cwd=working_dir)
    subprocess.call(['zip', '-r', './res/raw/seattle.zip', config_dir_rel], cwd=working_dir)
    subprocess.call(['zip', '-r', orig, './res'], cwd=working_dir)
    # Sign and align the apk
    subprocess.call(['jarsigner', '-digestalg', 'SHA1', '-sigfile', 'CERT', 
                     '-keystore', settings.ANDR_KEYSTORE_PATH, '-storepass',
                     settings.ANDR_KEYSTORE_PASS, '-keypass', settings.ANDR_KEY_PASS,
                     orig, settings.ANDR_KEY_NAME], cwd=working_dir)
    subprocess.call(['zipalign', '4', orig, align], cwd=working_dir)
    os.remove(orig)
    shutil.move(align, orig)

    shutil.rmtree(os.path.abspath(os.path.join(working_dir, 'res')))

  # Remove the working directories.
  shutil.rmtree(os.path.abspath(os.path.join(working_dir, constants.TEMP_DIR_NAMES['config_root'])))





# Internal functions to reduce redundancy in package_keys()

def write_key_file(user_name, user_key, directory, extension):
  key_filename = os.path.join(directory, user_name + extension)
  key_fileobj = open(key_filename, 'w')
  key_fileobj.write(user_key)
  key_fileobj.close()
  os.chmod(key_filename, constants.FILE_PERMISSIONS)

def write_key_bundle(working_dir, key_type):  
  bundle_filename = os.path.join(working_dir, constants.KEY_BUNDLES[key_type])
  bundle_directory = constants.TEMP_DIR_NAMES[key_type + '_keys']
  
  subprocess.call(['zip', '-r', '-', bundle_directory],
    cwd=working_dir,
    stdout=open(bundle_filename, 'wb'),
    stderr=open(os.devnull),
  )
  
  os.chmod(bundle_filename, constants.FILE_PERMISSIONS)
  
  return bundle_filename





def package_keys(user_data):
  """
  <Purpose>
    Uses the given user data to create two archives: one for the public
    keys of all users of the installer, and one for the private keys of
    all users created automatically by the installer.

  <Arguments>
    working_dir:
      The directory in which the installer configuration files are held, and
      where the key archives will be placed. Should be an absolute path.
      
    user_data:
      A dictionary of user information, with a key for each user name.
      Each user is represented by his own dictionary, including 'public_key'
      and possibly 'private_key' entries.

  <Exceptions>
    None.

  <Side Effects>
    Creates the key archives in the given build directory.

  <Returns>
    None.
  """
  
  working_dir = tempfile.mkdtemp()
  
  # Create the temporary directories to hold the key files.
  public_dir = os.path.join(working_dir, constants.TEMP_DIR_NAMES['public_keys'])
  private_dir = os.path.join(working_dir, constants.TEMP_DIR_NAMES['private_keys'])
    
  for dir_name in (public_dir, private_dir):
    if not os.path.isdir(dir_name):
      os.makedirs(dir_name, constants.DIR_PERMISSIONS)
      
  # Create the key files themselves.
  for name in user_data:
    # Create the public key file.
    write_key_file(name, user_data[name]['public_key'], public_dir, '.publickey')
        
    # Create the private key file, if the key exists.
    if user_data[name].get('private_key', None) is not None:
      write_key_file(name, user_data[name]['private_key'], private_dir, '.privatekey')

  # Record the filenames we use.
  bundle_filenames = dict()
         
  # Create the key bundles.
  bundle_filenames['public'] = write_key_bundle(working_dir, 'public')
  bundle_filenames['private']  = write_key_bundle(working_dir, 'private')
  
  # Remove the working directories.
  shutil.rmtree(public_dir)
  shutil.rmtree(private_dir)
  
  return bundle_filenames
