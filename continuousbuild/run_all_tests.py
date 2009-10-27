#!/usr/bin/env python
"""
<Program>
  run_all_tests.py

<Author>
  Justin Samuel
  
<Started>
  Oct 7, 2009
  
<Purpose>
  This script runs the tests in the "tests/" subdirectory, keeps a few old runs,
  and summarizes the results in an index.html file as well as an rss file of
  failures.

  This is a simple continuous integration system. We could use something fancier
  like buildbot or bitten someday if we have the time to do that. For now, this
  is just intended to run tests and summarize them on the same machine. No
  master-slave system.

  The idea is to cron this script to run every hour or so. It will generally
  notice if a copy is running (it will see a "running" directory that exists
  already), but you probably don't want to push your luck as after the "running"
  directory gets renamed, there could be a race. 
  
  It does make an attempt at stopping tests that are hung as well as child
  processes left over from tests. I haven't tested it too thoroughly, but I
  think it should be quite reliable at killing leftover children as long as
  the tests themselves are doing anything to create different session ids
  or group ids among their spawned processes.

  For the RSS file created, you may want to tell apache to send a different
  content-type header when it is requested. For example, add this to a
  .htaccess file:
    AddType 'application/rss+xml' rss

  If run through cron, cron should be setup to email output. This ensures
  that if this script itself fails, it will be known by some means other
  than noticing that the index.html page hasn't been updated recently.

  Note: you need to 'svn up' on your own outside of this script.
"""

import datetime
import glob
import os
import time
import shutil
import signal
import subprocess
import sys

import PyRSS2Gen


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




def remove_old_directories(latestrunnumber):
  # Rotate existing test results.
  for i in range(latestrunnumber - MAX_RUNS_KEPT * 2, latestrunnumber - MAX_RUNS_KEPT + 1):
    if os.path.exists(TESTLOG_DIR + "/" + str(i)):
      shutil.rmtree(TESTLOG_DIR + "/" + str(i))
  



def _write_svn_log(filename):
  logtext = subprocess.Popen(["svn", "log", TRUNK_DIR, "--limit", "1"],
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT).communicate()[0]
  revision = logtext.strip("-").strip().split()[0]
  open(filename, "w").write(revision + "\n")




def _get_and_increment_run_number():
  runfilename = TESTLOG_DIR + "/lastrun.txt"
  
  if not os.path.exists(runfilename):
    fd = open(runfilename, "w")
    fd.write("0")
    fd.close()
    
  fd = open(runfilename)
  newrunrumber = int(open(runfilename).read().strip()) + 1
  fd.close()
  
  fd = open(runfilename, "w")
  fd.write(str(newrunrumber))
  fd.close()
  
  return newrunrumber




def run_tests():
  
  if os.path.exists(TESTLOG_DIR + "/running/"):
    print "The 'running' directory already exists. Either another test is"
    print "running or one stopped in the middle. Either way, giving up."
    sys.exit(1)
    
  runnumber = _get_and_increment_run_number()
    
  os.mkdir(TESTLOG_DIR + "/running/")

  _write_svn_log(TESTLOG_DIR + "/running/svn.txt")
  
  # Run the individual tests.
  testrunnerlist = glob.glob(TEST_RUNNER_DIR + "/run_*")
  
  results = []
  failed_count = 0
  
  for testrunner in testrunnerlist:
    testname = os.path.basename(testrunner)

    if testname in SKIP_TEST_RUNNERS:
      results.append(["SKIPPED", testname, "", ""])
      continue

    logname = TESTLOG_DIR + "/running/" + testname + ".txt"
    proc = subprocess.Popen(['setsid', testrunner, TRUNK_DIR, logname],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    
    output = ""
    
    for runtime in range(MAX_TEST_TIME_SECONDS):
      if proc.poll() != None:
        retval = proc.returncode
        break
      time.sleep(1)
    else:
      retval = 9999
      output += "Test timed out.\n"

    # Make sure the process and all of its children are dead. This will not
    # kill this script because we put the testrunner on own session and thus
    # its own process group when we started it with setsid.
    try:
      # Note that I would think I should use the pgid returned from a call
      # to os.getpgid(proc.pid), but that actually seems to return the pgid
      # that is the pid of this script, which is not what I see with "ps".
      # That was when I tried os.getpgid(proc.pid) right after calling Popen,
      # though, so maybe that's part of it. However, the fact remains that
      # the pgid of the group we want to kill should be the pid of the process
      # we started with setsid. So, we'll use that processes' pid as the pgid.
      os.killpg(proc.pid, signal.SIGTERM)
      time.sleep(5)
      os.killpg(proc.pid, signal.SIGKILL)
    except OSError:
      pass
    
    output += proc.communicate()[0]
    
    if retval == 0:
      statusstr = "SUCCESS"
    else:
      statusstr = "FAILURE"
      failed_count += 1
      
    runtimestr = "(" + str(runtime) + " seconds)"
    results.append([statusstr, testname, runtimestr, output.strip()])
  
  
  # All tests done running. Generate the content of the summary file.
  # Format of summary file: 
  #   First line is 'SUCCESS' or 'FAILURE'.
  #   Second line is the time of the test run.
  #   Each additional line is the name of the tests followed by SUCCESS or
  #   FAILURE.
  
  summary_lines = []
  
  if failed_count == 0:
    summary_lines.append("SUCCESS" + "\n")
  else:
    summary_lines.append("FAILURE" + "\n")
  
  # Take off the microsecond so it doesn't get printed by isoformat().
  curdate = datetime.datetime.now().replace(microsecond=0)
  summary_lines.append(curdate.isoformat(' ') + "\n")
  
  for testresult in results:
    summary_lines += " ".join(testresult) + "\n"
  
  # Write the summary file.
  fd = open(TESTLOG_DIR + "/running/" + RESULTS_FILE_NAME, "w")
  fd.writelines(summary_lines)
  fd.close()
  
  os.rename(TESTLOG_DIR + "/running", TESTLOG_DIR + "/" + str(runnumber))

  return runnumber


  
  
def _get_all_results(latestrunnumber):
  """
  Returns a list of results from all past runs (including a run that
  was just done).
  """
  results = []
  
  for i in range(latestrunnumber, latestrunnumber - MAX_RUNS_KEPT, -1):
    if os.path.exists(TESTLOG_DIR + "/" + str(i)):
      fd = open(TESTLOG_DIR + "/" + str(i) + "/" + RESULTS_FILE_NAME)
      resultlines = fd.readlines()
      fd.close()
      
      fd = open(TESTLOG_DIR + "/" + str(i) + "/svn.txt")
      revision = fd.read().strip()
      fd.close()
      
      results.append([i, revision, resultlines])
    
  return results




def _create_rss_file(resultslist):
  
  failureitems = []
  for (runnumber, revision, resulttext) in resultslist:
    if resulttext[0].strip() != "SUCCESS":
      datestr = resulttext[1].strip()
      dateobj = datetime.datetime.strptime(datestr, "%Y-%m-%d %H:%M:%S")
      # The PyRSS2Gen module expects this to be in GMT, and python is a pain
      # for timezone conversion. I'll just hard code this to PST and ignore
      # daylight savings time.
      dateobj += datetime.timedelta(hours= -8)
      item = PyRSS2Gen.RSSItem(
         title="Test failure on run number " + str(runnumber) + " using " + revision,
         link=TESTLOG_URL,
         description="\n".join(resulttext),
         guid=PyRSS2Gen.Guid(TESTLOG_URL + datestr),
         pubDate=dateobj)
      failureitems.append(item)
  
  rss = PyRSS2Gen.RSS2(
    title="Test Failures on " + SYSTEM_DESCRIPTION,
    link=TESTLOG_URL,
    description="Seattle test failures for continuous build on " + SYSTEM_DESCRIPTION,
    lastBuildDate=datetime.datetime.now() + datetime.timedelta(hours= -8),
    items=failureitems)
  
  rss.write_xml(open(RSS_FILE_NAME + ".new", "w"))
  os.rename(RSS_FILE_NAME + ".new", RSS_FILE_NAME)




def _create_index_file(resultslist):
  htmllines = []
  
  htmllines.append("""
  <html>
  <head>
  <title>Seattle test log :: """ + SYSTEM_DESCRIPTION + """</title>
  <style>
    body { font-family : sans-serif; font-size : 100%; }
    h1 { font-size : 1.2em; }
    td, tr { font-size : 0.9em; }
    td { padding : 0 5px 0 5px; }
    table { border : 1px solid #555; }
    .date { white-space: nowrap; }
    .success { background-color : #afa; }
    .failure { background-color : #faa; }
  </style>
  </head>
  <body>
  <h1>""" + SYSTEM_DESCRIPTION + """</h1>
  <table>
  <th>#</th>
  <th>Date</th>
  <th>Revision</th>
  <th>Status</th>
  <th>Details</th>
  """)
  
  for (runnumber, revision, resulttext) in resultslist:
    if resulttext[0].strip() == "SUCCESS":
      htmllines.append('<tr class="success">')
    else:
      htmllines.append('<tr class="failure">')
    htmllines.append('<td>' + str(runnumber) + '</td>')
    # Date that is a link to the runnumber directory.
    htmllines.append('<td class="date"><a href="' + str(runnumber) + '/">' + 
                     resulttext[1].strip() + '<a></td>')
    # svn revision (e.g. r1234)
    htmllines.append('<td>' + revision + '</td>')
    # SUCCESS or FAILURE
    htmllines.append('<td>' + resulttext[0] + '</td>')
    # Everything after the date line.
    htmllines.append('<td>' + "<br />".join(resulttext[2:]) + '</td>')
    htmllines.append('</tr>')
      
  htmllines.append("""
  </table>
  </body>
  </html>
  """)
  
  open(TESTLOG_DIR + "/index.html.new", "w").write("\n".join(htmllines))
  os.rename(TESTLOG_DIR + "/index.html.new", TESTLOG_DIR + "/index.html")
  



def summarize_results(latestrunnumber):
  """
  This function may do things like create an index.html file. It could also
  email notifications or update a feed.
  """
  resultslist = _get_all_results(latestrunnumber)
  _create_index_file(resultslist)
  _create_rss_file(resultslist)




  
def main():
  # run the tests and put the output in a directory called "running".
  runnumber = run_tests()
  # Remove oldest directory, rename remaining ones, and rename the "running"
  # directory created by run_tests() to "1".
  remove_old_directories(runnumber)
  # Create the html and rss files.
  summarize_results(runnumber)
  
  

if __name__ == "__main__":
  main()
