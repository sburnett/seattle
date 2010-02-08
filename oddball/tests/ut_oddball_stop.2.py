import utfutil

def main():
           
  repy_args = ['--stop', 'repy.py', 
               '--status', 'foo',
               'restrictions.default', 
               'stop_testsleep.py'
               ]

  output = (out, error) = utfutil.execute_repy(repy_args)
  if not error or out: print 'FAIL'





if __name__ == '__main__':
  main()
