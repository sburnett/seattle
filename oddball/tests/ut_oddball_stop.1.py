import utfutil

def main():

  repy_args = [
               '--stop', 'nonexist', 
               '--status', 'foo',
               'restrictions.default', 
               'stop_testsleep.py'
               ]

  (out, error) = utfutil.execute_repy(repy_args)
  if out or error: print 'FAIL'





if __name__ == '__main__':
  main()
