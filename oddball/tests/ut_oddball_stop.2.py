import utfutil
import utf



def main():
           
  repy_args = ['--stop', 'repy.py', 
               '--status', 'foo',
               'restrictions.default', 
               'stop_testsleep.py'
               ]

  (rawout, error) = utfutil.execute_repy(repy_args)

  out = utf.strip_android_debug_messages(rawout)

  if not error or out: print 'FAIL'





if __name__ == '__main__':
  main()
