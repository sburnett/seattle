"""
<Program>
  run_tests.py

<Author>
  Justin Cappos

<Started>
  July 3rd, 2008

<Edits>
  Brent Couvrette - Updated so that it works with the new way of specifying
  ports dynamically.  Also changed how it is run, it now assumes you are 
  running it in a directory generated by running preparetest.py -t.  See
  usage for details.

  Cosmin Barsan 1-5-09 - Added the ability to run node manager tests by specifying the -n flag when running the script.
  
<Usage>
  To run the repy unit tests locally, first navigate to trunk, then 
  use these commands:

  1.  python preparetest.py -t <directory>
  2.  cd <directory>
  3.  python run_tests.py


  To run the node manager unit tests locally, open two shells (or command prompts). Navigate to trunk in each.
  
  1. On the FIRST command prompt type the following command
     python preparetest.py -t <directory>
     The -t flag must be included.
     
  2. On the SECOND command prompt enter the following sequence of commands:
     cd <directory>
     python nminit.py
     python nmmain.py
     
  3. On the FIRST command prompt, enter the follwing sequence of commands:
     cd <directory>
     python run_tests.py -n
     
<Description>
  python script to run the repy test cases locally...   Adapted from a bash script
  When the -n option is specified, the node manager tests are run instead of the repy tests.
 
  The types of repy tests are:
 
    s_*.py -- The correct result is the same as when run with python
    e_*.py -- The restricted program produces output on stderr (most likely
              because it throws an exception)
    z_*.py -- The restricted program produces no output 
    n_*.py -- The restricted program produces some output on stdout and no
              output on stderr
    b_*.py -- The restricted program produces output on both stderr and stdout
    u_*.py -- The result of running these programs is undefined.   They are
              not tested but may be useful as examples
    l_*.py -- Use circular logging while testing.   These test cases indicate
              an error by using exitall instead of letting the program 
              terminate normally...
 
  any of these types of tests may be preceeded by a 'r', which indicates that
  there is a specific restriction file for the test.   For example:
   re_foo_bar.py -- run the test (expecting an exception) with foo as the 
  restriction file.
  
  The node manager tests are:
  
    nmtest*.py -- nmmain.py must be running on a
              separate shell, or these tests will fail. These tests will throw
              an exception or produce output in the event they fail. All these
              tests use the restrictions.test restrictions file.
"""

import glob
import os
import sys
import shutil
import time

# Used to spawn subprocesses for tests. Fails on
# WindowsCE so we use WindowsAPI instead
try:
  import subprocess
  mobileNoSubprocess = False
except ImportError:
  # Set flag to avoid using subprocess
  mobileNoSubprocess = True 

  # import windows API
  import windows_api as windowsAPI
  pass
  
# Import repy constants for use in finding test files
import repy_constants

import testportfiller


# what we print at the end...
endput = ''

def run_test(testname):
  global passcount
  global failcount
  
  print "Running on: ", testname
  
  if testname.startswith('rs_') or testname.startswith('re_') or \
	testname.startswith('rz_') or testname.startswith('rn_') or \
	testname.startswith('rb_') or testname.startswith('rl_'):

    # must have three parts: r?_restrictionfn_testname.py
    if len(testname.split('_')) != 3:
      raise Exception, "Test name '"+testname+"' does not have 3 parts!"

    # take the 2nd character of the testname 'rs_' -> 's'
    testtype = testname[1]
    restrictfn = testname.split('_')[1]

  elif testname.startswith('s_') or testname.startswith('e_') or \
	testname.startswith('z_') or testname.startswith('n_') or \
	testname.startswith('b_') or testname.startswith('l_'):

    # take the 1st character of the testname 's_' -> 's'
    testtype = testname[0]
    restrictfn = "restrictions.default"
    
  elif testname.startswith('ru_') or testname.startswith('u_'):
    # Do not run undefined tests...
    return
  elif testname.startswith('nmtest'):
    testtype = 'z'
    restrictfn = "restrictions.test"
  else:
    raise Exception, "Test name '"+testname+"' of an unknown type!"


  logstream.write("Running test %-50s [" % testname)
  logstream.flush()
  result = do_actual_test(testtype, restrictfn, testname)

  if result:
    passcount = passcount + 1
    logstream.write(" PASS ]\n")
  else:
    failcount = failcount + 1
    logstream.write("FAILED]\n")
  logstream.flush()


def exec_command(command):
# Windows does not like close_fds and we shouldn't need it so...
  p =  subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

  # get the output and close
  theout = p.stdout.read()
  p.stdout.close()

  # get the errput and close
  theerr = p.stderr.read()
  p.stderr.close()

  # FreeBSD prints on stdout, when it gets a signal...
  # I want to look at the last line.   it ends in \n, so I use index -2
  if len(theout.split('\n')) > 1 and theout.split('\n')[-2].strip() == 'Terminated':
    # lose the last line
    theout = '\n'.join(theout.split('\n')[:-2])
    
    # however we threw away an extra '\n' if anything remains, let's replace it
    if theout != '':
      theout = theout + '\n'
    


  # everyone but FreeBSD uses stderr
  if theerr.strip() == 'Terminated':
    theerr = ''

  # Windows isn't fond of this either...
  # clean up after the child
#  os.waitpid(p.pid,0)

  return (theout, theerr)
  
def exec_repy_script(filename, restrictionsfile, arguments):
  global mobileNoSubprocess
  
  if not mobileNoSubprocess:
    return exec_command('python repy.py ' + arguments + ' ' + restrictionsfile + ' ' + filename)
  else:
    if os.path.isfile(repy_constants.PATH_SEATTLE_INSTALL + "execlog.out.old"):
      os.remove(repy_constants.PATH_SEATTLE_INSTALL + "execlog.out.old")
      
    repy_path =  repy_constants.PATH_SEATTLE_INSTALL + "repy.py"
    cmd = "--logfile execlog.out " + arguments + " --cwd \""+ repy_constants.PATH_SEATTLE_INSTALL + "\" " + restrictionsfile + " \"" + repy_constants.PATH_SEATTLE_INSTALL + filename + "\""
    print cmd
    childpid = windowsAPI.launchPythonScript(repy_path, cmd)
    
    # Wait for Child to finish execution
    windowsAPI.waitForProcess(childpid)
    
    time.sleep(5)
    
    theout = file(repy_constants.PATH_SEATTLE_INSTALL + "execlog.out.old", "r")
    output = theout.read()
    theout.close()
    
    return (output, '')
  
def do_actual_test(testtype, restrictionfn, testname):
  global endput
  global mobileNoSubprocess
  
  # match python
  if testtype == 's':
    if not mobileNoSubprocess:
      (pyout, pyerr) = exec_command('python '+testname)
      (testout, testerr) = exec_command('python repy.py --simple '+restrictionfn+" "+testname)
    else:
      # TODO: Read in captured tests and compare with exec repy script output?
      (testout, testerr) = exec_repy_script(testname, restrictionfn, "--simple ")
      pyout = testout
      pyerr = testerr
    
    capture_test_result(testname, pyout, pyerr, ".py")
    capture_test_result(testname, testout, testerr, ".repy")

    same = True

    if pyout != testout:
      # stdout differs
      endput = endput+testname+"\n"+ "standard out mismatch '"+pyout+"' != '"+testout+"'\n\n"
      same = False
    
    if pyerr != testerr:
      # stderr differs
      endput = endput+testname+"\n"+ "standard err mismatch '"+pyerr+"' != '"+testerr+"'\n\n"
      same = False
    
    return same

  # any out, no err...
  elif testtype == 'n':
    (testout, testerr) = exec_repy_script(testname, restrictionfn, "--status foo")
    if (not mobileNoSubprocess) and testout != '' and testerr == '':
      return True
    elif mobileNoSubprocess and testout != '' and testout.find('Traceback') == -1:
      return True
    else:
      endput = endput+testname+"\nout:"+testout+"err:"+ testerr+"\n\n"
      return False

  # any err, no out...
  elif testtype == 'e':
    (testout, testerr) = exec_repy_script(testname, restrictionfn, '--status foo')
    if (not mobileNoSubprocess) and testout == '' and testerr != '':
      return True
    elif mobileNoSubprocess and testout.find('Traceback') == -1:
      return True
    else:
      endput = endput+testname+"\nout:"+testout+"err:"+ testerr+"\n\n"
      return False

  # no err, no out...
  elif testtype == 'z':
    (testout, testerr) = exec_repy_script(testname, restrictionfn, '--status foo')
    if testout == '' and testerr == '':
      return True
    else:
      endput = endput+testname+"\nout:"+testout+"err:"+ testerr+"\n\n"
      return False

  # any err, any out...
  elif testtype == 'b':
    (testout, testerr) = exec_repy_script(testname, restrictionfn, '--status foo')
    if (not mobileNoSubprocess) and testout != '' and testerr != '':
      return True
    elif mobileNoSubprocess and testout.find('Traceback') == -1:
      return True
    else:
      endput = endput+testname+"\nout:"+testout+"err:"+ testerr+"\n\n"
      return False

  # no err, no out (logging)...
  elif testtype == 'l':
    # remove any existing log
    try:
      os.remove("experiment.log.old")
      os.remove("experiment.log.new")
    except OSError:
      pass

    # run the experiment
    if not mobileNoSubprocess:
      (testout, testerr) = exec_command('python repy.py --logfile experiment.log --status foo '+restrictionfn+" "+testname)
    else:
      (testout, testerr) = exec_repy_script(testname, restrictionfn, "--status foo")

    # first, check to make sure there was no output or error
    if mobileNoSubprocess or (testout == '' and testerr == ''):
      if not mobileNoSubprocess:
        try:
          myfo = file("experiment.log.old","r")
          logdata = myfo.read()
          myfo.close()
          if os.path.exists("experiment.log.new"):
            myfo = file("experiment.log.new","r")
            logdata = logdata + myfo.read()
            myfo.close()

          # use only the last 16KB
          logdata = logdata[-16*1024:]

        except:
          endput = endput+testname+"\nCan't read log!\n\n"
          return False
      else:
        logdata = testout
        
      if "Fail" in logdata:
        endput = endput+testname+"\nString 'Fail' in logdata\n\n"
        return False 
      elif "Success" not in logdata:
        endput = endput+testname+"\nString 'Success' not in logdata\n\n"
        return False 
      else:
        return True

    else:
      endput = endput+testname+"\nHad output or errput! out:"+testout+"err:"+ testerr+"\n\n"
      return False

  else: 
    raise Exception, "Unknown test type '"+str(testout)+"'"


    

def do_oddballtests():
  global passcount
  global failcount
  global endput
  # oddball "stop" tests...
  logstream.write("Running test %-50s [" % "Stop Test 1")
  logstream.flush()

  (testout, testerr) = exec_repy_script("stop_testsleep.py", "restrictions.default", "--stop nonexist --status foo")
  if testout == '' and testerr == '':
    passcount = passcount + 1
    logstream.write(" PASS ]\n")
  else:
    failcount = failcount + 1
    endput = endput+"Stop Test 1\noutput or errput! out:"+testout+"err:"+ testerr+"\n\n"
    logstream.write("FAILED]\n")



  # oddball "stop" test2...
  logstream.write("Running test %-50s [" % "Stop Test 2")
  logstream.flush()

  (testout, testerr) = exec_repy_script("stop_testsleep.py", "restrictions.default", '--stop repy.py --status foo')
  if (not mobileNoSubprocess) and testout == '' and testerr != '':
    passcount = passcount + 1
    logstream.write(" PASS ]\n")
  elif mobileNoSubprocess and testout.find('Traceback') == -1:
    passcount = passcount + 1
    logstream.write(" PASS ]\n")
  else:
    failcount = failcount + 1
    logstream.write("FAILED]\n")
    endput = endput+"Stop Test 2\noutput or no errput! out:"+testout+"err:"+ testerr+"\n\n"


  # remove the junk file...
  try:
    os.remove("junk_test.out")
  except: 
    pass


  # oddball "stop" test3...
  logstream.write("Running test %-50s [" % "Stop Test 3")
  logstream.flush()

  (testout, testerr) = exec_repy_script('stop_testsleepwrite.py', "restrictions.default", '--stop junk_test.out --status foo')
  if testout == '' and testerr == '':
    passcount = passcount + 1
    logstream.write(" PASS ]\n")
  else:
    failcount = failcount + 1
    logstream.write("FAILED]\n")
    endput = endput+"Stop Test 3\noutput or errput! out:"+testout+"err:"+ testerr+"\n\n"

def setup_test_capture():
  global captureDir
  
  current_dir = os.getcwd()
  
  if not os.path.isdir(captureDir):
    print "Given capture directory is not a valid directory"
    sys.exit(1)
    
  #set working directory to the test folder
  os.chdir(captureDir)	
  files_to_remove = glob.glob("*")

  #clean the test folder
  for f in files_to_remove: 
    if os.path.isdir(f):
      shutil.rmtree(f)		
    else:
      os.remove(f)
      
  # Pop back to current directory
  os.chdir(current_dir)
  
# Captures the output of a test and puts it into the log file
def capture_test_result(testname, pyout, pyerr, additionalExt=""):
  global captureOutput
  global captureDir
  
  # Ignore if we're not capturing output
  if not captureOutput:
    return None
    
  current_dir = os.getcwd()
  
  # Change to directory and write file
  os.chdir(captureDir)
  fileh = file(testname + additionalExt + ".out", "w")
  fileh.write(pyout)
  fileh.close()
  
  fileh = file(testname + additionalExt + ".err", "w")
  fileh.write(pyerr)
  fileh.close()
  
  # Pop back to test directory
  os.chdir(current_dir)
  
if len(sys.argv) > 1 and sys.argv[1] == '-q':
  logstream = file("test.output","w")
  sys.argv = sys.argv[1:]
else:
  logstream = sys.stdout

print "1, Current Dir: ", os.getcwd()  
# If boolean is true, then unit test output will be
# captured and stored
captureOutput = False
captureDir = None
if len(sys.argv) > 1 and sys.argv[1] == '-ce':
  captureOutput = True
  captureDir = sys.argv[2]
  sys.argv = sys.argv[2:]
  setup_test_capture()
  
# these are updated in run_test
passcount=0
failcount=0

# Have the testportfiller fill in all of the messport/connport
# tags with default values so that the tests can be successfully
# run locally. - Brent
testportfiller.main()

# for each test... run it!
# if the -n flag is specified, only run node manager tests
if (len(sys.argv) > 1 and sys.argv[1] == '-n') or (len(sys.argv) > 2 and sys.argv[2] == '-n'):
  for testfile in glob.glob("nmtest*.py"):
    run_test(testfile)
else:
  print "Current Dir: ", os.getcwd()
  for testfile in glob.glob("rs_*.py") + glob.glob("rn_*.py") + \
  	  glob.glob("rz_*.py") + glob.glob("rb_*.py") + glob.glob("ru_*.py") + \
	  glob.glob("re_*.py") + glob.glob("rl_*.py") +glob.glob("s_*.py") + \
	  glob.glob("n_*.py") + glob.glob("z_*.py") + glob.glob("b_*.py") + \
	  glob.glob("u_*.py") + glob.glob("e_*.py") + glob.glob("l_*.py"):
    run_test(testfile)
    
  do_oddballtests()

print "Done running"
print >> logstream, passcount,"tests passed,",failcount,"tests failed"

# only print if there is something to print
if endput:
  print endput

print "Quiting"
time.sleep(120)