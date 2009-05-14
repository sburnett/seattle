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
  
  Armon Dadgar 3-5-09 - Added new flag "-cpu" that runs a special set of tests to check CPU throttling
  
  Armon Dadgar 4-6-9- Added new flag "-threaderr" that runs a special test to check for the proper behavior of 
  repy when the system thead limit is reached. This may destabilize some systems, so save everything!

  Armon Dadgar 4-21-9- Added new flag "-network" that runs special tests to check for the proper behavior of 
  repy when given "--ip" and "--iface" flags.
  
  Armon Dadgar 4-28-9- Added new flag "-nm-network" that runs special tests to check for the proper behavior of 
  the nodemanager when ip and iface preferences are enabled.
   
<Usage>
  To run the repy unit tests locally, first navigate to trunk, then 
  use these commands:

  1.  python preparetest.py -t <directory>
  2.  cd <directory>
  3.  python run_tests.py


  To run the CPU throttling checks, use these commands:
  1.  python preparetest.py -t <directory>
  2.  cd <directory>
  3.  python run_tests.py -cpu
  
  To run the Threading error checks, use these commands:
  1.  python preparetest.py -t <directory>
  2.  cd <directory>
  3.  python run_tests.py -threaderr

  To run the Network Restrictions checks, use these commands:
  1.  python preparetest.py -t <directory>
  2.  cd <directory>
  3.  python run_tests.py -network

  To run the Node Manager network restrictions checks, use these commands:
  1.  python preparetest.py -t <directory>
  2.  cd <directory>
  3.  python run_tests.py -nm-network

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
  
  The n, e, z, b and u tests can be prefixed with "py_" to indicate that this is 
  a python unit test, and not a repy unit test. Ex: py_z_test_foo.py
  
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

def run_test(fulltestname):
  global passcount
  global failcount
  
  #print "Running on: ", testname
  
  #Is this a python or repy unit test?
  is_python_test = False
  if fulltestname.startswith('py_'):
    is_python_test = True
    testname = fulltestname[3:]
  else:
    testname = fulltestname
  
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


  logstream.write("Running test %-50s [" % fulltestname)
  logstream.flush()
  result = do_actual_test(testtype, restrictfn, fulltestname, is_python_test)

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
  
def exec_repy_script(filename, restrictionsfile, arguments={}, script_args=''):
  global mobileNoSubprocess
  
  if script_args != '':
    script_args = ' ' + script_args
  
  if not mobileNoSubprocess:
    # Convert arguments
    arg_string = arguments_to_string(arguments)
    
    return exec_command('python repy.py ' + arg_string + restrictionsfile + ' ' + filename + script_args)
  else:
    if os.path.isfile(repy_constants.PATH_SEATTLE_INSTALL + "execlog.out.old"):
      os.remove(repy_constants.PATH_SEATTLE_INSTALL + "execlog.out.old")
    if os.path.isfile(repy_constants.PATH_SEATTLE_INSTALL + "execlog.out.new"):
      os.remove(repy_constants.PATH_SEATTLE_INSTALL + "execlog.out.new")      

    # Set default values
    arguments.setdefault("logfile", "execlog.out")
    arguments.setdefault("cwd", "\"" + repy_constants.PATH_SEATTLE_INSTALL + "\"")
    
    # Convert arguments
    arg_string = arguments_to_string(arguments)
      
    repy_path =  "\"" + repy_constants.PATH_SEATTLE_INSTALL + "repy.py" + "\""
    cmd = arg_string + restrictionsfile + " \"" + repy_constants.PATH_SEATTLE_INSTALL + filename + "\"" + script_args
    #print cmd
    childpid = windowsAPI.launchPythonScript(repy_path, cmd)
    
    # Wait for Child to finish execution
    windowsAPI.waitForProcess(childpid)
    
    time.sleep(5)

    if os.path.isfile(repy_constants.PATH_SEATTLE_INSTALL + "execlog.out.old"):
        theout = file(repy_constants.PATH_SEATTLE_INSTALL + "execlog.out.old", "r")
        output = theout.read()
        theout.close()
    else:
        output = ''
    
    return (output, '')
    
def arguments_to_string(arguments):
  order = ['simple', 'ip', 'iface','nootherips','logfile', 'stop', 'status', 'cwd', 'servicelog']
  argument_string = ""
  
  for key in order:
    try:
      value = arguments.pop(key)
      if value != '':
        value += ' '
      argument_string += "--" + key + " " + value
    except KeyError:
      pass
      
  # If there are still items left then just append them
  if len(arguments) > 0:
    for name in arguments:
      value = arguments[name]
      if value != '':
        value += ' '
      argument_string += name + " " + value

  return argument_string
  
def do_actual_test(testtype, restrictionfn, testname, is_python_test):
  global endput
  global mobileNoSubprocess
  
  # match python
  if testtype == 's':
    if not mobileNoSubprocess:
      (pyout, pyerr) = exec_command('python '+testname)
      (testout, testerr) = exec_repy_script(testname, restrictionfn, {'simple':''})
    else:
      # TODO: Read in captured tests and compare with exec repy script output?
      (testout, testerr) = exec_repy_script(testname, restrictionfn, {'simple':''})
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
    if is_python_test:
      (testout, testerr) = exec_repy_script(testname, '')
    else:
      (testout, testerr) = exec_repy_script(testname, restrictionfn, {'status':'foo'})
    
    capture_test_result(testname, testout, testerr, ".repy")
    
    if (not mobileNoSubprocess) and testout != '' and testerr == '':
      return True
    elif mobileNoSubprocess and testout != '' and testout.find('Traceback') == -1:
      return True
    else:
      endput = endput+testname+"\nout:"+testout+"err:"+ testerr+"\n\n"
      return False

  # any err, no out...
  elif testtype == 'e':
    if is_python_test:
      (testout, testerr) = exec_repy_script(testname, '')
    else:
      (testout, testerr) = exec_repy_script(testname, restrictionfn, {'status':'foo'})
    
    capture_test_result(testname, testout, testerr, ".repy")
    
    if (not mobileNoSubprocess) and testout == '' and testerr != '':
      return True
    elif mobileNoSubprocess and testout.find('Traceback') != -1:
      return True
    else:
      endput = endput+testname+"\nout:"+testout+"err:"+ testerr+"\n\n"
      return False

  # no err, no out...
  elif testtype == 'z':
    if is_python_test:
      (testout, testerr) = exec_command("python " + testname)
    else:
      (testout, testerr) = exec_repy_script(testname, restrictionfn, {'status':'foo'})
    
    capture_test_result(testname, testout, testerr, ".repy")
    
    if testout == '' and testerr == '':
      return True
    else:
      endput = endput+testname+"\nout:"+testout+"err:"+ testerr+"\n\n"
      return False

  # any err, any out...
  elif testtype == 'b':
    if is_python_test:
      (testout, testerr) = exec_repy_script(testname, '')
    else:
      (testout, testerr) = exec_repy_script(testname, restrictionfn, {'status':'foo'})
    
    capture_test_result(testname, testout, testerr, ".repy")
    
    if (not mobileNoSubprocess) and testout != '' and testerr != '':
      return True
    elif mobileNoSubprocess and testout.find('Traceback') != -1:
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
      (testout, testerr) = exec_repy_script(testname, restrictionfn, {'logfile':'experiment.log', 'status':'foo'})
    else:
      (testout, testerr) = exec_repy_script(testname, restrictionfn, {'status':'foo'})
      
    capture_test_result(testname, testout, testerr, ".repy")

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

  (testout, testerr) = exec_repy_script("stop_testsleep.py", "restrictions.default", {'stop':'nonexist', 'status':'foo'})
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

  (testout, testerr) = exec_repy_script("stop_testsleep.py", "restrictions.default", {'stop':'repy.py', 'status':'foo'})
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

  (testout, testerr) = exec_repy_script('stop_testsleepwrite.py', "restrictions.default", {'stop':'junk_test.out','status':'foo'})
  if testout == '' and testerr == '':
    passcount = passcount + 1
    logstream.write(" PASS ]\n")
  else:
    failcount = failcount + 1
    logstream.write("FAILED]\n")
    endput = endput+"Stop Test 3\noutput or errput! out:"+testout+"err:"+ testerr+"\n\n"


  import nonportable
  running_on_windows = nonportable.ostype in ["Windows", "WindowsCE"]

  # oddball killing the parent test...
  logstream.write("Running test %-50s [" % "Kill Repy resource monitor.")
  logstream.flush()

  # Get the location of python
  if not running_on_windows:
    locationproc = subprocess.Popen("which python",shell=True,stdout=subprocess.PIPE)
    locationproc.wait()
    location = locationproc.stdout.read().strip()
    locationproc.stdout.close()

    # Start the test
    p =  subprocess.Popen((location+" repy.py restrictions.default killp_writetodisk.py").split(),stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
  # Windows proc object  
  else:
    p = subprocess.Popen("python repy.py restrictions.default killp_writetodisk.py",shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)

  pid = p.pid

  # Wait a bit 
  time.sleep(3)
  
  # Kill the repy resource monitor
  nonportable.portablekill(pid)

  # Make sure the file size is not changing
  firstsize = os.path.getsize("junk_test.out")
  time.sleep(1)
  secondsize = os.path.getsize("junk_test.out")

  if firstsize == secondsize:
    passcount = passcount + 1
    logstream.write(" PASS ]\n")
  else:
    failcount = failcount + 1
    logstream.write("FAILED]\n")
    endput = endput+"Killing Repy's resource monitor did not stop repy!\n\n"
  
  # Close the pipes
  p.stdout.close()
  p.stderr.close()

def setup_test_capture():
  global captureDir
  
  current_dir = os.getcwd()
  
  if not os.path.isdir(captureDir):
    print "Given capture directory is not a valid directory"
    sys.exit(1)
    
  #set working directory to the test folder
  os.chdir(captureDir)	
  files_to_remove = glob.glob("*.out") + glob.glob("*.err")

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

# If boolean is true, then unit test output will be
# captured and stored
captureOutput = False
captureDir = None
if len(sys.argv) > 1 and sys.argv[1] == '-ce':
  captureOutput = True
  captureDir = sys.argv[2]
  sys.argv = sys.argv[2:]
  setup_test_capture()
  
# Check for the CPU flag
# This is a constant for the benchmark interval, how many seconds are used to
# determine the maximum number of iterations at full CPU
CPU_TEST_TIME = 10 
if len(sys.argv) > 1 and sys.argv[1] == "-cpu":
  # Define mini helper function to run the CPU test
  def run_cpu_test(suffix, flag, num):
    (testout, testerr) = exec_repy_script('special_testcputhrottle.py', 'restrictions.'+suffix, {}, flag + " " + num)
    return testout.rstrip("\n")
  
  # Get the max iterations
  logstream.write("Running test %-50s [" % ("100% CPU, Determine cycles, "+str(CPU_TEST_TIME)+" sec"))
  logstream.flush()
  iterations_at_fullcpu = run_cpu_test("fullcpu","-t",str(CPU_TEST_TIME))
  logstream.write(iterations_at_fullcpu.rjust(6)+"]\n")
  
  # Run test at 10% cpu
  logstream.write("Running test %-50s [" % "10%  CPU, Run Cycles")
  logstream.flush()  
  time_at_10percent = round(float(run_cpu_test("default","-n",iterations_at_fullcpu)), 2)
  logstream.write(str(time_at_10percent).rjust(6)+"s]\n")
  
  # Run test at 25% cpu
  logstream.write("Running test %-50s [" % "25%  CPU, Run Cycles")
  logstream.flush()  
  time_at_25percent = round(float(run_cpu_test("quartercpu","-n",iterations_at_fullcpu)),2)
  logstream.write(str(time_at_25percent).rjust(6)+"s]\n")
  
  # Run test at 50% cpu  
  logstream.write("Running test %-50s [" % "50%  CPU, Run Cycles")
  logstream.flush()
  time_at_50percent = round(float(run_cpu_test("halfcpu","-n",iterations_at_fullcpu)),2)
  logstream.write(str(time_at_50percent).rjust(6)+"s]\n")

  # Run test at 100% cpu
  logstream.write("Running test %-50s [" % "100% CPU, Run Cycles")
  logstream.flush()  
  time_at_100percent = round(float(run_cpu_test("fullcpu","-n",iterations_at_fullcpu)), 2)
  logstream.write(str(time_at_100percent).rjust(6)+"s]\n")
  
  # Print status report
  logstream.write("Real Slow-down should be (semi-)close to Linear, and Relative should be close to 1.\nRelative is the time speedup compared to the increase in cpu from the previous test.\n")
  logstream.write("10% CPU, Linear: 1000% Real: "+str(round(time_at_10percent/time_at_100percent*100,2))+"%\n")
  logstream.write("25% CPU, Linear: 400%  Real: "+str(round(time_at_25percent/time_at_100percent*100,2))+"% Relative: "+str(round((10*time_at_10percent/25)/time_at_25percent, 2))+"\n")  
  logstream.write("50% CPU, Linear: 200%  Real: "+str(round(time_at_50percent/time_at_100percent*100,2))+"% Relative: "+str(round((25*time_at_25percent/50)/time_at_50percent, 2))+"\n")
  logstream.write("100% CPU, Linear: 100%  Real: "+str(round(time_at_100percent/time_at_100percent*100,2))+"% Relative: "+str(round((50*time_at_50percent/100)/time_at_100percent, 2))+"\n")
  logstream.flush()
  exit()


# Check for the thread error flag, and if found
# run the proper threading test, then exit
if len(sys.argv) > 1 and sys.argv[1] == "-threaderr":
  # Check if there are any old status files
  files = glob.glob("threadtest_status-*")
  for elem in files: # Remove each status file
    os.remove(elem)
  
  # Print some info
  start = time.time()
  logstream.write("INFO: Please be patient. This may take awhile to complete. Start time: "+str(start)+"\n")
  
  # First, run the test
  (testout, testerr) = exec_repy_script("testthreadingerr.repy", "restrictions.insane", {'status':'threadtest_status'})
  
  # Check for the status file
  files = glob.glob("threadtest_status-*")
  statfile = files[0] # There should only be 1 status file...
  
  if not "ThreadErr" in statfile:
    logstream.write("FAILURE: Expected status file to have ThreadErr state. Statfile:  "+statfile+"\n")
  else:
    logstream.write("SUCCESS: Status file has ThreadErr state. Statfile:  "+statfile+"\n")
  
  # Print an end time
  end = time.time()
  diff = end-start
  logstream.write("INFO: End Time: "+str(end)+"  Elapsed Time: "+str(diff)+"s\n")
  
  # Exit now
  exit()
  
# Check for the network flag, and if found
# run the proper tests, then exit
if len(sys.argv) > 1 and sys.argv[1] == "-network":
  # Mini-function to make life easier
  def run_network_test(name, args):
    logstream.write("INFO: Running: "+name+"\n")
    # Run the tests
    (testout, testerr) = exec_repy_script(name, "restrictions.default", args)
    # Check for output
    if testout != "" or testerr != "":
        logstream.write("FAILURE: Out:\n"+testout+"\n\nErr:\n"+testerr+"\n")
  
  # Checks that getmyip returns only loopback and is bindable, using ip flag
  run_network_test("ip_onlyloopback_checkgetmyip.py", {'ip':'127.0.0.1','nootherips':''})

  # Checks that we only get loopback and is bindable, using iface flag
  run_network_test("ip_nopreferred_noallowed_checkgetmyip.py", {'iface':'lo','nootherips':''})
  
  # Checks that we only get loopback and is bindable, without any flags other than nootherips
  run_network_test("ip_nopreferred_noallowed_checkgetmyip.py", {'nootherips':''})     

  # Checks that given a junk IP this is not returned by getmyip
  run_network_test("ip_junkip_checkgetmyip.py", {'ip':'256.256.256.256','nootherips':''})
  
  # Checks that we are not allowed to bind to a junk IP (the test uses a different IP)
  run_network_test("ip_junkip_trybind.py", {'ip':'256.256.256.256','nootherips':''})

  # Run interface test, this one passes many common interfaces to the test, and
  # tests that we can get a non-loopback and bindable address from getmyip
  logstream.write("INFO: Running: ip_multiple_iface_trybind.py. This may fail since it relies on the system having an interface that I provided.\n")
  (out, err) = exec_command('python repy.py --iface eth0 --iface eth1 --iface en0 --iface en1 --iface xl0 --iface xl1 \
  --iface "Ethernet adapter Local Area Connection" --iface "Ethernet adapter Local Area Connection 2" \
  --nootherips restrictions.default ip_multiple_iface_trybind.py')
  if out != "" or err != "":
      logstream.write("FAILURE: Out:\n"+out+"\n\nErr:\n"+err+"\n")
      
  logstream.write("INFO: Done.\n")

  # Exit now
  exit()

# Check for the nodemanager network flag, and if found
# run the proper tests, then exit
if len(sys.argv) > 1 and sys.argv[1] == "-nm-network":
  # This is to find the NM PID
  import runonce
  
  # First run nmminit
  exec_command("python nminit.py")
  
  # Pre-process our helper file
  exec_command("python repypp.py helper_uploadstartprintlog.repy helper_uploadstartprintlog.py")
  
  # We need getmyip()
  import misc
  DEFAULT_IP = misc.getmyip()
  LOOPBACK_IP = "127.0.0.1"
  JUNK_IP = "128.0.0.255"
  
  # We need nonportable to check for network sockets
  import nonportable
  
  # Get the osAPI
  osAPI = nonportable.osAPI
  
  # We need this to change the nm configuration file
  import injectconfig
  
  allowed_port = 50000
  # First override the ports, only use one port, so we know what to check
  injectconfig.inject('ports', [allowed_port], "nodeman.cfg")
  
  # The NM will use a constant key, store this
  NET_KEY = 'networkrestrictions'
  
  # Create generic config dictionary
  config = {}
  config['nm_restricted'] = False
  config['nm_user_preference'] = []
  config['repy_restricted'] = False
  config['repy_nootherips'] = False
  config['repy_user_preference'] = []
  
  # Starts the NM after injecting the config for NET_KEY
  def start_nm(name, config):
    logstream.write("INFO: Running: "+name+"\n")
    # Override the configuration
    injectconfig.inject(NET_KEY, config, "nodeman.cfg")
    # Start the NM
    p =  subprocess.Popen("python nmmain.py", shell=True)
    # Wait a bit for everything to settle
    time.sleep(3)
  
  # Stops the NM, allowed time for cleanup to occur
  def stop_nm():
    # Stop the NM
    gotlock = runonce.getprocesslock("seattlenodemanager")
    if gotlock == True:
      # No NM running? This is an error
      logstream.write("FAILURE: Successfully acquired the NM process lock! The NM should be running!\n")
    else:
      if gotlock:
        # Kill the NM
        nonportable.portablekill(gotlock)
        # Allow the sockets to cleanup and the locks to be cleaned
        time.sleep(3)
  
  # Starts the NM, checks that it is bound to a certain IP/Port, stops the NM  
  def run_network_test(name, config, ip):
    start_nm(name, config)
    
    # Check for a network socket
    isListen = osAPI.existsListeningNetworkSocket(ip, allowed_port, True)
    
    # Check for output
    if not isListen:
        logstream.write("FAILURE: Expected NM to listen on IP:"+ip+" and port:"+str(allowed_port)+"! \n")
    
    stop_nm()
  
  # Starts the NM, lauches a repy script which then lauches our specified script
  # the scripts test repy's behavior given various ip/iface flags
  # We check to make sure there was no output produced, then stop the NM
  def run_repy_param_test(name, config):
    start_nm(name, config)
    
    # Wait for the NM to get ready to handle requests, this can sometimes mess up the timing
    # since the NM launches a ton of threads at start time
    time.sleep(5) 
    
    # Launch our helper repy script, give it the name of the file
    (testout, testerr) = exec_repy_script("helper_uploadstartprintlog.py", "restrictions.test", {}, name)

    # Check for output
    if testout != "" or testerr != "":
        logstream.write("FAILURE: Out:\n"+testout+"\n\nErr:\n"+testerr+"\n")
    stop_nm()
    
  ### First check the NM binding behavior  
  
  # Run with the generic config, no restrictions
  run_network_test("No Restrictions, defaults on.", config, DEFAULT_IP)
  
  # Run with the generic config, enable restrictions
  config['nm_restricted'] = True
  run_network_test("Enable Restrictions, nothing provided.", config, LOOPBACK_IP)
  
  # Run with the default IP, enable restrictions
  config['nm_user_preference'] = [(True, DEFAULT_IP)]
  run_network_test("Enable Restrictions, provided IP from getmyip().", config, DEFAULT_IP)
  
  # Run with the junk IP, enable restrictions
  config['nm_user_preference'] = [(True, JUNK_IP)]
  run_network_test("Enable Restrictions, provided junk IP.", config, LOOPBACK_IP)

  # Run interface test, this one passes many common interfaces to the test, and
  # tests that we can get a non-loopback and bindable address from getmyip
  config['nm_user_preference'] = [(False, 'eth0'),(False, 'eth1'),(False, 'en0'),(False, 'en1')\
                                  ,(False, 'xl0'),(False, 'xl1'),(False, 'Ethernet adapter Local Area Connection')\
                                  ,(False, 'Ethernet adapter Local Area Connection 2') ]
  run_network_test("Enable Restrictions, provided common Interfaces. May fail!", config, DEFAULT_IP)



  ### Check that the NM is passing the correct parameters to repy
  # NOTE: See the -network flag for more. This is running those same
  # tests, but through the NM with repy preferences
  
  # Reverse the changes
  config['nm_restricted'] = False
  config['nm_user_preference'] = []
  injectconfig.inject('ports', [1224], "nodeman.cfg") # Restore the normal port
  
  # Checks that getmyip returns only loopback and is bindable, using ip flag
  config['repy_restricted'] = True
  config['repy_nootherips'] = True
  
  # Checks that we only get loopback and is bindable, without any flags other than nootherips
  run_repy_param_test("ip_nopreferred_noallowed_checkgetmyip.py", config)

  # Checks that getmyip returns only loopback and is bindable, using ip flag
  config['repy_user_preference'] = [(True, "127.0.0.1")]
  run_repy_param_test("ip_onlyloopback_checkgetmyip.py", config)

  # Checks that we only get loopback and is bindable, using iface flag
  config['repy_user_preference'] = [(False, "lo")]
  run_repy_param_test("ip_nopreferred_noallowed_checkgetmyip.py", config)

  # Checks that given a junk IP this is not returned by getmyip
  config['repy_user_preference'] = [(True, "256.256.256.256")]
  run_repy_param_test("ip_junkip_checkgetmyip.py", config)
  
  # Checks that we are not allowed to bind to a junk IP (the test uses a different IP)
  run_repy_param_test("ip_junkip_trybind.py", config)
  
  # Checks given many common interfaces that we get a non loopback IP that is bindable
  config['repy_user_preference'] = [(False, 'eth0'),(False, 'eth1'),(False, 'en0'),(False, 'en1')\
                                  ,(False, 'xl0'),(False, 'xl1'),(False, 'Ethernet adapter Local Area Connection')\
                                  ,(False, 'Ethernet adapter Local Area Connection 2') ]
  run_repy_param_test("ip_multiple_iface_trybind.py", config)
  
  # I'm reusing the same test, but instead of a list of interfaces, I'm just giving it the OS default IP
  # It should work the same anyways
  config['repy_user_preference'] = [(True, DEFAULT_IP)]
  run_repy_param_test("ip_multiple_iface_trybind.py", config)
  
  logstream.write("INFO: Done.\n")

  # Exit now
  exit()

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
  for testfile in glob.glob("rs_*.py") + glob.glob("rn_*.py") + \
  	  glob.glob("rz_*.py") + glob.glob("rb_*.py") + glob.glob("ru_*.py") + \
	  glob.glob("re_*.py") + glob.glob("rl_*.py") +glob.glob("s_*.py") + \
	  glob.glob("n_*.py") + glob.glob("z_*.py") + glob.glob("b_*.py") + \
	  glob.glob("u_*.py") + glob.glob("e_*.py") + glob.glob("l_*.py") + \
    glob.glob("py_n_*.py") + glob.glob("py_z_*.py") + glob.glob("py_b_*.py") + \
    glob.glob("py_u_*.py") + glob.glob("py_e_*.py"):
    run_test(testfile)
  
  do_oddballtests()

print >> logstream, passcount,"tests passed,",failcount,"tests failed"

# only print if there is something to print
if endput:
  print endput
