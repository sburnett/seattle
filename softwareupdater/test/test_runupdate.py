"""
<Program>
  test_runupdate.py

<Author>
  Brent Couvrette
  couvb@cs.washington.edu

<Start date>  
  October 19, 2008

<Purpose>
  This will actually run all of the softwareupdater tests.  Everything must be
  already setup via the test_updater.py script, and the updater site specified
  as an argument must contain the folders created by that same script.
  test_updater.py documents the proceedures for making sure this happens.

<Usage>
  python test_runupdate.py <baseurl>

  Where baseurl is the url which contains the subdirectories created by
  test_updater.py.
  
<Note>
  When running these tests on Windows, ps cannot be used to check process 
  status.  You will have to do this yourself in the task manager.
"""

import subprocess
import sys
import time
import glob
import shutil
import platform

import test_rsync

def runRsyncTest(testtype, updateurl, otherargs=[]):
  """
  <Purpose>
    Runs a test on the rsync-like portion of the software updater.
  <Arguments>
    testtype - The type of rsync test to run.  Test types are reproduced here:
        -u <filename1 filename2 ... >    Test will assert that all of the given 
                                         filenames were updated correctly.
        -x                     Test will assert that no updates have been made
        -e                     Test will assert that there was a proper		                               Exception thrown

    updateurl - The url which contains the subdirectories created by
        test_updater.py.
    otherargs - The list of file names necesary for the -u test type.  Should
        be empty (the default) for any other test type.
  """
  # Run the test
  rsync = subprocess.Popen(['python', 'test_rsync.py', testtype]+otherargs+[updateurl], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    
  # Get the output
  theout = rsync.stdout.read()
  rsync.stdout.close()

  # Return the output
  return theout


def main():
  if len(sys.argv) < 2:
    print 'Must supply base url!'
    sys.exit(1)

  baseurl = sys.argv[1]
  ############################
  # Run the rsync only tests #
  ############################

  # Run the noup test (Nothing should fail, nothing should be updated)
  print runRsyncTest('-x', baseurl+'noup/')

  # Run the wronghash test(There should be an RsyncError, and no updates)
  print runRsyncTest('-e', baseurl+'wronghash/')
  
  # Run the badkeysig test (There should be no updates)
  print runRsyncTest('-x', baseurl+'badkeysig/')

  # Run the corruptmeta test (there should be an RsyncError, and no updates)
  print runRsyncTest('-e', baseurl+'corruptmeta/')

  # Run the updatenmmain test (only nmmain should get updated)
  print runRsyncTest('-u', baseurl+'updatenmmain/', ['nmmain.py', 'metainfo'])
  
  # Run an update that should get us into a state where the softwareupdater has
  # a different key than what the metainfo is signed with.  The next test will
  # ensure that our method of dealing with this situation works.
  print runRsyncTest('-u', baseurl+'updater/', ['softwareupdater.py', 'metainfo'])
  
  # Run an update that should successfully update from the strange state from
  # the previous test.
  print runRsyncTest('-u', baseurl+'updater_new/', ['nmmain.py', 'metainfo'])

  #####################################
  # Finished running rsync only tests #
  #####################################

  # Copy back everything from noup so the restart tests start with a 
  # clean slate.
  for originalfile in glob.glob('../noup/*'):
    shutil.copy(originalfile, originalfile[8:])

  ##################################
  # Software updater restart tests #
  ##################################
  # Keep track of whether ps is there (it isn't on Windows)
  no_ps = False
  
  # NOTE: This intentionally doesn't use the superior checking mechanism in
  # nonportable because we don't want to import potentially broken modules...
  if platform.system() == 'Windows' or platform.system() == 'Microsoft':
    # If we are running on windows, disable the ps calls.
    no_ps = True
    
  updateprocess = subprocess.Popen(['python', 'softwareupdater.py'])
  if not no_ps:
    # Only do the ps check if ps is available
    ps = subprocess.Popen('ps -ef | grep "python softwareupdater.py" | grep -v grep', shell=True, stdout=subprocess.PIPE)
    psout = ps.stdout.read()
    print 'Initial ps out:'
    print psout
    if psout == '':
      print 'Failure to start initially'

  # Wait for 2 minutes for the update to happen and the
  # process to die.
  for junk in range(60):
    if updateprocess.poll() != None:
      break
    time.sleep(2)

  ret = updateprocess.returncode
  print 'Return code is: '+str(ret)
  if ret != 10:
    print 'Wrong return code! '+str(ret)
  else:
    pass
    if not no_ps:
      # Only do the ps check if ps is available
      ps = subprocess.Popen('ps -ef | grep "python softwareupdater.py" | grep -v grep', shell=True, stdout=subprocess.PIPE)
      psout = ps.stdout.read()
      psout.strip()
      print 'After ps out:'
      print psout
      if psout == '':
        print 'New updater failed to start!'
      else:
        print 'softwareupdater restart success!'

  # Wait 2 minutes for the second update to happen.
  # Is there a way to get a handle for the new softwareupdater?
  time.sleep(120)

  # If nmmain's version has been updated, the second update was a success!
  nmmainfile = file('nmmain.py', 'r')
  nmmaindata = nmmainfile.read()
  nmmainfile.close()
  if 'version = "1234"' in nmmaindata:
    print 'Second update a success!'
  else:
    print 'Second update failed to happen within 2 minutes'

  ######################################
  # End Software updater restart tests #
  ######################################

if __name__ == '__main__':
  main()
