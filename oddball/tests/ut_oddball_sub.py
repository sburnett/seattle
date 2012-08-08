import os
import utf
import utfutil

def main():
  # Test running repy from a sub directory
  tmp_directory = 'subdirtest'

  # Make a temporary directory
  if not os.path.exists(tmp_directory): os.mkdir(tmp_directory)

  repy_args = [
               '--cwd', tmp_directory,
               '../restrictions.default',
               '../test_init.py',
              ]

  (rawout, error) = utfutil.execute_repy(repy_args)

  out = utf.strip_android_debug_messages(rawout)

  if out or error: print 'FAIL'



if __name__ == '__main__':
  main()

