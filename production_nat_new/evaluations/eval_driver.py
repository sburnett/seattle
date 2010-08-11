import subprocess 
import time

def shellrun(cmd):
  proc = subprocess.Popen(cmd, shell=True,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE)
  return proc.communicate()[0]


timestable = ''
memstable = ''

for i in range(1):
  if i % 5 == 0:
    timestable += '\n%d,' % i
    memstable += '\n%d,' % i

    for attempt in range(10):
      output = shellrun("python eval_client.py %d" % i).strip()
      (t, m) = output.split(',')
      timestable += '%s,' % t
      memstable += '%s,' % m

      print i,attempt
 
    # f = open('times.csv', 'a')
    # f.write(timestable + '\n')
    # f.close()

    # f = open('mems.csv', 'a')
    # f.write(memstable + '\n')
    # f.close()

print timestable
print '\n' * 3
print memstable
