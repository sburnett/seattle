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

  Before running this script, edit the values in the config.py file in the same
  directory as this script in order to configure various important values,
  including where files should be written to.

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

import config





def remove_old_directories(latestrunnumber):
  # Rotate existing test results.
  for i in range(latestrunnumber - config.MAX_RUNS_KEPT * 2, latestrunnumber - config.MAX_RUNS_KEPT + 1):
    if os.path.exists(config.TESTLOG_DIR + "/" + str(i)):
      shutil.rmtree(config.TESTLOG_DIR + "/" + str(i))
  



def _write_svn_log(filename):
  logtext = subprocess.Popen(["svn", "log", config.TRUNK_DIR, "--limit", "1"],
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT).communicate()[0]
  revision = logtext.strip("-").strip().split()[0]
  open(filename, "w").write(revision + "\n")




def _get_and_increment_run_number():
  runfilename = config.TESTLOG_DIR + "/lastrun.txt"
  
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
  
  if os.path.exists(config.TESTLOG_DIR + "/running/"):
    print "The 'running' directory already exists. Either another test is"
    print "running or one stopped in the middle. Either way, giving up."
    sys.exit(1)
    
  runnumber = _get_and_increment_run_number()
    
  os.mkdir(config.TESTLOG_DIR + "/running/")

  _write_svn_log(config.TESTLOG_DIR + "/running/svn.txt")
  
  # Run the individual tests.
  testrunnerlist = glob.glob(config.TEST_RUNNER_DIR + "/run_*")
  
  results = []
  failed_count = 0
  
  for testrunner in testrunnerlist:
    testname = os.path.basename(testrunner)

    if testname in config.SKIP_TEST_RUNNERS:
      results.append(["SKIPPED", testname, "", ""])
      continue

    logname = config.TESTLOG_DIR + "/running/" + testname + ".txt"
    proc = subprocess.Popen(['setsid', testrunner, config.TRUNK_DIR, logname],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    
    output = ""
    
    for runtime in range(config.MAX_TEST_TIME_SECONDS):
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
  fd = open(config.TESTLOG_DIR + "/running/" + config.RESULTS_FILE_NAME, "w")
  fd.writelines(summary_lines)
  fd.close()
  
  os.rename(config.TESTLOG_DIR + "/running", config.TESTLOG_DIR + "/" + str(runnumber))

  return runnumber


  
  
def _get_all_results(latestrunnumber):
  """
  Returns a list of results from all past runs (including a run that
  was just done).
  """
  results = []
  
  for i in range(latestrunnumber, latestrunnumber - config.MAX_RUNS_KEPT, -1):
    if os.path.exists(config.TESTLOG_DIR + "/" + str(i)):
      fd = open(config.TESTLOG_DIR + "/" + str(i) + "/" + config.RESULTS_FILE_NAME)
      resultlines = fd.readlines()
      fd.close()
      
      fd = open(config.TESTLOG_DIR + "/" + str(i) + "/svn.txt")
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
      # for timezone conversion. I'll just hard code assuming the system's in
      # PST and ignore daylight savings time.
      dateobj += datetime.timedelta(hours=8)
      item = PyRSS2Gen.RSSItem(
         title="Test failure on run number " + str(runnumber) + " using " + revision,
         link=config.TESTLOG_URL,
         description="\n".join(resulttext),
         # Spaces aren't valid in a guid.
         guid=PyRSS2Gen.Guid(config.TESTLOG_URL + str(runnumber)),
         pubDate=dateobj)
      failureitems.append(item)
  
  rss = PyRSS2Gen.RSS2(
    title="Test Failures on " + config.SYSTEM_DESCRIPTION,
    link=config.TESTLOG_URL,
    description="Seattle test failures for continuous build on " + config.SYSTEM_DESCRIPTION,
    lastBuildDate=datetime.datetime.now() + datetime.timedelta(hours=8),
    items=failureitems)
  
  rss.write_xml(open(config.RSS_FILE_NAME + ".new", "w"))
  os.rename(config.RSS_FILE_NAME + ".new", config.RSS_FILE_NAME)




def _create_index_file(resultslist):
  htmllines = []
  
  htmllines.append("""
  <html>
  <head>
  <title>Seattle test log :: """ + config.SYSTEM_DESCRIPTION + """</title>
  <meta http-equiv="refresh" content='""" + str(config.META_REFRESH_INTERVAL) + """' />
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
  <h1>""" + config.SYSTEM_DESCRIPTION + """</h1>
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
  
  open(config.TESTLOG_DIR + "/index.html.new", "w").write("\n".join(htmllines))
  os.rename(config.TESTLOG_DIR + "/index.html.new", config.TESTLOG_DIR + "/index.html")
  



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
