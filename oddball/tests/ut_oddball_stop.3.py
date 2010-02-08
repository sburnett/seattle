import os

import utfutil

def main():
  # clean up the stop file if it already exists.
  if os.path.exists('junk_test.out'): os.remove('junk_test.out')

  repy_args = [
               '--stop', 'junk_test.out',
               '--status', 'foo',
               'restrictions.default', 
               'stop_testsleepwrite.py'
               ]

  (out, error) = utfutil.execute_repy(repy_args)
  if out or error: print 'FAIL'




if __name__ == '__main__':
  main()
