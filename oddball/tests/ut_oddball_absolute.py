import os

import utfutil

def main():

  # Absolute Path Stop Test
  stop_file = 'junk_test.out'

  # Clean up the stop file if it already exists.
  if os.path.exists(stop_file): os.remove(stop_file)

  current_directory = os.getcwd()
  stop_file = os.path.join(current_directory, stop_file)

  repy_args = ['--stop', stop_file, 
               '--status', 'foo',
               'restrictions.default',
               'stop_testsleepwrite.py']

  result = (out, error) = utfutil.execute_repy(repy_args)

  if os.path.exists(stop_file): os.remove(stop_file)

  if out or error: 
    print 'FAIL'




if __name__ == '__main__':
  main()
