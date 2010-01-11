"""
A very basic run tests for the purpose of this project only

"""


import subprocess
import os
import shutil
import signal
import time

# launch three echo servers for testing
def run_nat_forwarder():
  args = ['python','repy.py','restrictions.eric','Nat_Forwarder.repy','127.0.0.1','12345']
  
  return subprocess.Popen(args)
  

def run_test(testname,counts):



  # set up arguments
  args = ['python','repy.py','restrictions.test',testname]
  stdout_file = open('output/'+testname+'.out','w')
  stderr_file = open('output/'+testname+'.err','w')


  
  subprocess.call(args,stdout=stdout_file,stderr=stderr_file)
  stdout_file.close()
  stderr_file.close()  

 
  #open the output files for reading
  out = open('output/'+testname+'.out','r')
  out_str = out.read()
  out.close()
  err = open('output/'+testname+'.err','r')
  err_str = err.read()
  err.close()

  if len(err_str)> 0 or len(out_str) > 0:
    print testname+'\t\t[FAILED]'
    print ''
    print 'std out: '+out_str
    print 'std err: '+err_str
    counts['failcount'] +=1
  else:
    print testname+'\t\t[PASSED]'
    
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
    if testfile[0:5] == "test_":
      #runner = run_nat_forwarder()    
      run_test(testfile,counts)
      #os.kill(runner.pid,signal.SIGKILL)
  

  print counts['passcount'],"tests passed,",counts['failcount'],"tests failed"

 



#start testmain if we are being initialized
if __name__ == '__main__':
	testmain()

