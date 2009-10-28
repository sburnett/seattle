"""
Configuration info for the continuous build run_all_tests.py script.
"""

import os
import sys



# A description of the system these tests are running on.
SYSTEM_DESCRIPTION = "OS_NAME_HERE (python " + sys.version.split()[0] + ")"

# The directory where all results will be stored. This should probably be
# a web-accessible directory.
TESTLOG_DIR = "/tmp/testlogs"

# A file kept in Teach tests results directory (e.g. TESTLOG_DIR/1/) which
# contains a summary of individual tests that run.  The first line of this
# file will be SUCCESS or FAILURE to indicate whether all tests passed or
# some did not. 
RESULTS_FILE_NAME = "results.txt"

# An rss feed with failure info. This should probably be in the TESTLOG_DIR
# or at least at some other location that is web-accessible.
RSS_FILE_NAME = TESTLOG_DIR + "/failures.rss"

TESTLOG_URL = "http://localhost/testlog/"

# The number of directories of test results to keep in TESTLOG_DIR.
MAX_RUNS_KEPT = 100

# Amount of time before giving up on a test.
MAX_TEST_TIME_SECONDS = 60 * 15

# By default we assume that this file is testing the checked out copy of trunk
# that it resides in. This is really just for development.  If you want to be
# able to automatically propagate changes to systems running this from the
# latest from svn, we'd need to move some of the configuration settings out to
# a different file, lest they be clobbered with the default settings from the
# svn copy.
# This should be an absolute path, not a relative one.
TRUNK_DIR = os.path.realpath(os.path.dirname(__file__))

# Each file in this directory that starts with "run_" will be considered a test
# to be run. Each script should execute with a non-zero status if the tests
# failed. Each script is passed two arguments when executed: the TRUNK_DIR and
# name of a file that all of it's stdout and stderr output should be written
# to (this will be an absolute path).
TEST_RUNNER_DIR = TRUNK_DIR + "/continuousbuild/tests"

# A list of test runners (just their basenames) that shouldn't be run.
SKIP_TEST_RUNNERS = []

# Number of seconds between automatic refreshes of the index.html page.
META_REFRESH_INTERVAL = 300
