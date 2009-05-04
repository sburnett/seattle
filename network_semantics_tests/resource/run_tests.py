import subprocess
import os
import shutil
import signal
import time

# launch three echo servers for testing
def run_echo_servers():
  args = ['python','repy.py','restrictions.default','echo_server.py','127.0.0.1','12345']
  runners = [] 
  runners.append(subprocess.Popen(args))
  args[4] = '127.0.0.2'
  runners.append(subprocess.Popen(args))
  args[4] = '127.0.0.3'
  runners.append(subprocess.Popen(args))
  
  return runners


def run_test(testname,counts):



  # set up arguments
  args = ['python','repy.py','restrictions.default',testname]
  stdout_file = open('output/'+testname+'.out','w')
  stderr_file = open('output/'+testname+'.err','w')


  # TODO run echo servers if required
  #if 'SERVER' in testname:
  #  runners = run_echo_servers()
  #  print 'RUNNING echo server'
  #  time.sleep(1)

  subprocess.call(args,stdout=stdout_file,stderr=stderr_file)
  stdout_file.close()
  stderr_file.close()  
  
  # TODO kill the echo servers if started
  #if 'SERVER' in testname:
  #  for runner in runners:
  #    os.kill(runner.pid,signal.SIGKILL)
  #    print 'killed '+str(runner.pid)
  #  time.sleep(1)

 
  #open the output files for reading
  out = open('output/'+testname+'.out','r')
  out_str = out.read()
  out.close()
  err = open('output/'+testname+'.err','r')
  err_str = err.read()
  err.close()

  if len(err_str)> 0 or len(out_str) > 0:
    print testname+'  FAILED'
    counts['failcount'] +=1
  else:
    #no errors occured so remove this files
    os.remove('output/'+testname+'.out')
    os.remove('output/'+testname+'.err')
    counts['passcount'] +=1
 



#carry out all of the tests
def testmain():


  # these are updated in run_test
  counts = {}
  counts['passcount']=0
  counts['failcount']=0
	

  # for each test... run it!
  for testfile in os.listdir('.'):
    # TODO, should be able to run SERVER tests
    if testfile[0:5] == "test_" and 'MANUAL' not in testfile and 'SERVER' not in testfile:
      run_test(testfile,counts)
    

  print counts['passcount'],"tests passed,",counts['failcount'],"tests failed"

 



#start testmain if we are being initialized
if __name__ == '__main__':
	testmain()

