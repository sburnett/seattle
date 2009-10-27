#!/bin/bash

# Author: Justin Samuel
# Date started: 9 July 2009
# 
# This script must be run from the same directory that preparetest.py is
# in (that is, from trunk).
#
# This script may not fully work and the comments at the top here may be out of sync
# with the code. This was an attempt to make running the software updater remote tests
# not a pain, but really those tests weren't that useful, anyway.
#
# This is just a convenience script for preparing to run the remote software
# updater tests. It will run preparetest.py and create the necessary
# empty subdirectory in the target test directory location.
#
# This will not run the tests because more work needs to be done after the
# tests are prepared.
#
# Usage:
#   ./softwareupdater/prepare_remote_tests.sh name_of_directory_to_put_tests_in url_on_your_webserver
#
# Note: some of the tests will fail if you start out with /tmp/runoncelock.softwareupdater.* files
#       on your system, even if the software updater is not running.
#
# Example of all steps, including using this script:
#   mkdir /tmp/remotetestfiles
#   cd /path/to/trunk
#   ./softwareupdater/test/prepare_remote_tests.sh /tmp/remotetestfiles http://seattle.cs.washington.edu/jsamuel/updatertest/
#   scp -r /tmp/remotetestfiles/* seattle:public_html/updatertest/
#   cd /tmp/remotetestfiles/mytestdir    # Note: 'mytestdir' was created in there by prepare_remote_tests.sh
#   python test_updater_remote.py http://seattle.cs.washington.edu/jsamuel/updatertest/
#   rm -Rf /tmp/remotetestfiles
#   # Clean up your files on the remote server.

testsdir="$1"
remoteurl="$2"

if [ "$testsdir" == "" ] || [ "$remoteurl" == "" ]; then
  echo "Usage: ./softwareupdater/prepare_remote_tests.sh name_of_directory_to_put_tests_in url_on_your_webserver"
  exit 1
fi

if [ ! -d "$testsdir" ]; then
  echo "The tests directory you specified for use doesn't exist. Please create it."
  exit 1
fi

lastcharacter=${remoteurl#${remoteurl%?}}
if [ "$lastcharacter" != "/" ]; then
  echo "The last character of the url must be a '/'"
  exit 1
fi

if [ ! -d "softwareupdater" ]; then
  echo "This script must be run from the same directory that preparetest.py is in."
  echo "Usage: ./softwareupdater/prepare_remote_tests.sh name_of_directory_to_put_tests_in url_on_your_webserver"
  exit 1
fi

# ps -ef is probably linux-specific. Somewhere there was a note about ps -aww for Darwin.
if [ "`ps -ef | grep softwareupdater.py | grep -v grep`" != "" ]; then
  echo "Aborting because there is an instance of softwarepdater.py already running."
  echo "Note: Even though this script wouldn't start the tests, you're going to need to stop any running"
  echo "      software updaters before you can run the tests, so this is just a strong reminder."
  exit 1
fi

# Create empty subdirectory 'mytestdir' in $testsdir
mkdir $testsdir/mytestdir

python preparetest.py $testsdir/mytestdir

# Copy extra files needed for the tests.
cp -R softwareupdater/test/* $testsdir/mytestdir

cd $testsdir/mytestdir

python test_updater_remote.py $remoteurl

echo
echo "Now it's your turn:"
echo 
echo "You must copy the contents of the directory $testsdir to the remote webserver."
echo "The contents of the directory must be accessible at $remoteurl"
echo "That is, you should end up with the following valid urls:"
echo "   ${remoteurl}mytestdir"
echo "   ${remoteurl}noup"
echo "   and so on."
echo
echo "When you've done that, do the following:"
echo "    cd $testsdir/mytestdir"
echo "    python test_runupdate.py $remoteurl"
echo
