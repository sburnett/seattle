""" 
Author: Justin Cappos

Start Date: Sept 1st, 2008

Description:
Utility function for sleeping without waking early...


"""

import time 

# sleep for a specified time.  Don't return early (no matter what)
def do_sleep(waittime):

  # there might be a race here
  endtime = time.time() + waittime
  sleeptime = endtime - time.time()
  while sleeptime>0:
    time.sleep(sleeptime)
    sleeptime = endtime - time.time()

      

