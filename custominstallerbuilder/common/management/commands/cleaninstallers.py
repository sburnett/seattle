"""
<Program Name>
  cleaninstallers.py

<Started>
  December 2010

<Author>
  Alex Hanson

<Purpose>
  A django-admin command to remove all pre-built installers, but leave the
  vesselinfo files intact. This command should be run whenever new base
  installers are put into place.

  Example usage:
	  /path/to/custominstallerbuilder/local/manage.py cleaninstallers
"""

import os
import shutil
from optparse import make_option

from django.conf import settings
from django.core.management.base import NoArgsCommand, CommandError

import custominstallerbuilder.common.constants as constants
import custominstallerbuilder.common.packager as packager
from custominstallerbuilder.common.logging import log_exception


class Command(NoArgsCommand):
  help = 'Removes all custom installers, allowing new ones to be built upon request.'
  option_list = NoArgsCommand.option_list + (
      make_option('--purge',
          action='store_true',
          dest='purge',
          default=False,
          help='Purge all custom installer data, including the vesselinfo files and cryptographic keys.'),
      )
  
  def handle_noargs(self, **options):
    try:
      directory_listing = os.listdir(settings.CUSTOM_INSTALLER_ROOT)
      
      for entry_name in directory_listing:
        build_directory = os.path.join(settings.CUSTOM_INSTALLER_ROOT, entry_name)
        vesselinfo_filename = os.path.join(build_directory, 'vesselinfo')

        # We assume that if the base installers directory is in the mix, it
        # doesn't have a vesselinfo file. Therefore, it will automatically be spared.
        if os.path.isdir(build_directory) and os.path.isfile(vesselinfo_filename):
          
          # If the purge option is set, delete the whole directory.
          if options['purge']:
            shutil.rmtree(build_directory)
            continue
          
          # Otherwise, just remove the installers.
          for platform in constants.PLATFORM_BUNDLES:
            installer_filename = os.path.join(build_directory, constants.PLATFORM_BUNDLES[platform])
            
            if os.path.isfile(installer_filename):
              os.remove(installer_filename)

      if options['purge']:
        print 'All custom installer data is now removed. Users will not be able to access their previous builds.'
      else:
        print 'All custom installers are now removed. New installers will be generated upon request.'
        
    except:
      log_exception()          
      raise CommandError('Unable to remove custom installers!')
