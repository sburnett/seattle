#!/usr/bin/env bash

# Author: Justin Samuel
# Date started: 9 July 2009
#
# This script must be run from the same directory that preparetest.py is
# in (that is, from trunk).
#
# This is just a convenience script to do preparetests, do the additional work
# needed for running the software updater tests locally, and then run them.
#
# Note: some of the tests will fail if you start out with /tmp/runoncelock.softwareupdater.* files
#       on your system, even if the software updater is not running.
#
# Usage:
#   ./softwareupdater/run_local_tests.sh name_of_directory_to_put_tests_in

testsdir="$1"

if [ "$testsdir" == "" ]; then
  echo "Usage: ./softwareupdater/test/run_local_tests.sh name_of_directory_to_put_tests_in"
  exit 1
fi

if [ ! -d "$testsdir" ]; then
  echo "The tests directory you specified for use doesn't exist. Please create it."
  exit 1
fi

if [ ! -d "softwareupdater" ]; then
  echo "This script must be run from the same directory that preparetest.py is in."
  echo "Usage: ./softwareupdater/test/run_local_tests.sh name_of_directory_to_put_tests_in"
  exit 1
fi

# ps -ef is probably linux-specific. Somewhere there was a note about ps -aww for Darwin.
if [ "`ps -ef | grep softwareupdater.py | grep -v grep`" != "" ]; then
  echo "Can't start tests: there is an instance of softwarepdater.py already running."
  exit 1
fi

python preparetest.py $testsdir 

# Copy the extra files that must be in the tests directory for the local software updater tests.
cp -R softwareupdater/test/* $testsdir
cp -R assignments/webserver/* $testsdir

# Change to the tests directory.
cd $testsdir

# Run the tests.
python test_updater_local.py

