"""
<Program Name>
  constants.py

<Started>
  December 2010

<Author>
  Alex Hanson

<Purpose>
  A collection of constants used throughout other files of the Custom Installer
  Builder.
"""

import os


# The complete set of platforms supported by the Custom Installler Builder.
PLATFORMS = set(['linux', 'mac', 'windows', 'android'])

# For each platform listed above, it should belong to one of the following
# sets.
TGZ_PLATFORMS = set(['linux', 'mac'])
ZIP_PLATFORMS = set(['windows'])
APK_PLATFORMS = set(['android'])

# For each platform listed above, provide the name of the base installer
# archive that will be used to construct customized installers.
PLATFORM_BUNDLES = {
  'linux': 'seattle_linux.tgz',
  'mac': 'seattle_mac.tgz',
  'windows': 'seattle_win.zip',
  'android': 'seattle_android.apk',
}

# The names for generated cryptographic key bundles.
KEY_BUNDLES = {
  'public': 'public_keys.zip',
  'private': 'private_keys.zip',
}

# The names of temporary subdirectories used during the packaging process.
TEMP_DIR_NAMES = {
  'config_root': 'seattle',
  'config': os.path.join('seattle', 'seattle_repy'),
  'public_keys': 'public_keys',
  'private_keys': 'private_keys',
}

# The rules which govern what constitutes a valid username.
USERNAME_RULES = {
  'min_length': 3,
  'max_length': 40,
  
  # Specifies all alphanumeric characters, as well as the underscore.
  'valid_chars': r'0-9a-zA-Z_',
  
  # Specifies all alphanumeric characters.
  'valid_first_chars': r'0-9a-zA-Z',
}

# The form which build IDs should take. This is used for validation and URL
# pattern matching. Matches a string of exactly 40 characters, composed
# entirely of digits and lowercase letters.
BUILD_ID_REGEX = r'[a-z0-9]{40}'

# The default permissions for newly created files or directories.
FILE_PERMISSIONS = 0644
DIR_PERMISSIONS = 0755

