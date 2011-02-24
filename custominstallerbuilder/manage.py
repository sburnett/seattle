#!/usr/bin/env python
"""
<Program Name>
  manage.py

<Started>
  December 2010

<Author>
  Alex Hanson

<Purpose>
  An extended version of the stock manage.py created by Django. Most users will
  not already have the custominstallerbuilder module in their Python path, so
  this script checks if that is the case. If the module can not be found, the
  script adds its own parent directory to the Python path and checks again.
  
  The script itself can be used for many Django administrative tasks, including
  the custom 'manage.py cleaninstallers' command included with this software.
  Try 'manage.py help' or 'manage.py help <command>' for more information.
"""

import os
import sys

from django.core.management import execute_manager


try:
  # If this fails, try to automatically adjust the path.
  import custominstallerbuilder
except ImportError:
  # Assume this file exists in the main project directory, which should be named
  # 'custominstallerbuilder'. Add the parent of the project directory to the
  # Python path.
  PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
  sys.path.append(os.path.abspath(os.path.join(PROJECT_ROOT, '..')))


try:
  import custominstallerbuilder
except ImportError:
  sys.stderr.write("Module 'custominstallerbuilder' cannot be found in the Python path, nor could it be automatically added.\n")
  sys.exit(1)


try:
  import custominstallerbuilder.local.settings as settings
except ImportError:
  sys.stderr.write("Error: Unable to import 'custominstallerbuilder.local.settings'\n")
  sys.stderr.write("You might trying copying the 'local_template' directory to 'local' if that directory does not exist. Otherwise, check your 'local/settings.py' file for errors.\n")
  sys.exit(1)


if __name__ == '__main__':
  execute_manager(settings)
