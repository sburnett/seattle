The continuous build scripts assume the following:

  1. You have copied the following two scripts out to the same directory as
     svn trunk is checked out to (that is, all of the files in the same
     directory as this README file):
     * cron_run_tests.sh
     * run_all_tests.py
     * PyRSS2Gen.py
     
  2. All of the trunk/continuousbuild/tests/run_* files executable. They don't
     have to be python scripts, they can be shell scripts, too, so we don't
     invoke them as python scripts but instead of executables.
     
  3. You have set the appropriate configuration settings in run_all_tests.py
     for the system you are running this on.
     
  4. You have setup the cron_run_tests.sh script to be run by a user who has
     write access to the TESTLOG_DIR and TRUNK_DIR you have defined in
     run_all_tests.py
     
With this setup, you will not need to make changes to the system for
additional testrunners added to the continuousbuild/tests directory
but you will need to manually update run_all_tests.py on any systems
it is running when you make changes to it in svn.
