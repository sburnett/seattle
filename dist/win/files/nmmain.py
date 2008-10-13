""" 
Author: Justin Cappos

Module: Node Manager main program.   It initializes the other modules and
        doesn't do much else.

Start date: September 3rd, 2008

This is the node manager for Seattle.   It ensures that sandboxes are correctly
assigned to users and users can manipulate those sandboxes safely.   

The design goals of this version are to be secure, simple, and reliable (in 
that order).   

The node manager has several different threads.   

   An advertisement thread (nmadverise) that inserts entries into OpenDHT so 
that users and owners can locate their vessels.
   A status thread (nmstatusmonitor) that checks the status of vessels and 
updates statuses in the table used by the API.
   An accept thread (nmconnectionmanager) listens for connections (preventing
simple attacks) and puts them into a list.
   A worker thread (used in the nmconnectionmanager, nmrequesthandler, nmAPI)
handles enacting the appropriate actions given requests from the user.
   The main thread initializes the other threads and monitors them to ensure
they do not terminate prematurely (restarting them as necessary).

"""

import time

import threading

import nmadvertise

import nmstatusmonitor

import nmconnectionmanager

# need to initialize the name, key and version (for when we return information
# about us).   Also we need the dictionary of vessel state so that the threads
# can update / read it.
import nmrequesthandler

import persist

import misc


# One problem we need to tackle is should we wait to restart a failed service
# or should we constantly restart it.   For advertisement and status threads, 
# I've chosen to wait before restarting...   For worker and accept, I think
# it's essential to keep restarting them as often as we can...
#
# these variables help us to track when we've started and whether or not we
# should restart

# the last time the thread was started
thread_starttime = {}

# the time I should wait
thread_waittime = {}

# never wait more than 5 minutes
maxwaittime = 300.0

# or less than 2 seconds
minwaittime = 2.0

# multiply by 1.5 each time...
wait_exponent = 1.5

# and start to decrease only after a reasonable run time...
reasonableruntime = 30

# and drop by
decreaseamount = .5



# BUG: what if the data on disk is corrupt?   How do I recover?   What is the
# "right thing"?   I could run nminit again...   Is this the "right thing"?

version = "0.1a"

# Our settings
configuration = {}



# has the thread started?
def should_start_waitable_thread(threadid, threadname):
  # first time!   Let's init!
  if threadid not in thread_starttime:
    thread_waittime[threadid] = minwaittime
    thread_starttime[threadid] = 0.0

  # If it has been started, and the elapsed time is too short, always return
  # False to say it shouldn't be restarted
  if thread_starttime[threadid] and time.time() - thread_starttime[threadid] < thread_waittime[threadid]:
    return False
    
  for thread in threading.enumerate():
    if threadname in str(thread):
      # running now.   If it's run for a reasonable time, let's reduce the 
      # wait time...
      if time.time() - thread_starttime[threadid] > reasonableruntime:
        thread_waittime[threadid] = max(minwaittime, thread_waittime[threadid]-decreaseamount)
      return False
  else:
    return True

# this is called when the thread is started...
def started_waitable_thread(threadid):
  thread_starttime[threadid] = time.time()
  thread_waittime[threadid] = min(maxwaittime, thread_waittime[threadid] ** wait_exponent)

  


# has the thread started?
def is_accept_thread_started():
  for thread in threading.enumerate():
    if 'AcceptThread' in str(thread):
      return True
  else:
    return False


def start_accept_thread():
  # do this until we get the AcceptThread started...
  while True:

    if is_accept_thread_started():
      # if it has chosen a port, 
      if nmconnectionmanager.portused != None: 
          # what is my name (for advertisements)
          myname = str(misc.getmyip()) + ":" + str(nmconnectionmanager.portused)

          # we're done, return the name!
          return myname

    else:
      # start the AcceptThread and set it to a daemon.   I think the daemon 
      # setting is unnecessary since I'll clobber on restart...
      acceptthread = nmconnectionmanager.AcceptThread(misc.getmyip(), configuration['ports'])
      acceptthread.setDaemon(True)
      acceptthread.start()


    # check infrequently
    time.sleep(configuration['pollfrequency'])
  






# has the thread started?
def is_worker_thread_started():
  for thread in threading.enumerate():
    if 'WorkerThread' in str(thread):
      return True
  else:
    return False



def start_worker_thread(sleeptime):

  if not is_worker_thread_started():
    # start the WorkerThread and set it to a daemon.   I think the daemon 
    # setting is unnecessary since I'll clobber on restart...
    workerthread = nmconnectionmanager.WorkerThread(sleeptime)
    workerthread.setDaemon(True)
    workerthread.start()


# has the thread started?
def is_advert_thread_started():
  for thread in threading.enumerate():
    if 'Advertisement Thread' in str(thread):
      return True
  else:
    return False


def start_advert_thread(vesseldict, myname):

  if should_start_waitable_thread('advert','Advertisement Thread'):
    # start the AdvertThread and set it to a daemon.   I think the daemon 
    # setting is unnecessary since I'll clobber on restart...
    advertthread = nmadvertise.advertthread(vesseldict)
    nmadvertise.myname = myname
    advertthread.setDaemon(True)
    advertthread.start()
    started_waitable_thread('advert')
  


def is_status_thread_started():
  for thread in threading.enumerate():
    if 'Status Monitoring Thread' in str(thread):
      return True
  else:
    return False


def start_status_thread(vesseldict,sleeptime):

  if should_start_waitable_thread('status','Status Monitoring Thread'):
    # start the StatusThread and set it to a daemon.   I think the daemon 
    # setting is unnecessary since I'll clobber on restart...
    statusthread = nmstatusmonitor.statusthread(vesseldict,sleeptime)
    statusthread.setDaemon(True)
    statusthread.start()
    started_waitable_thread('status')
  



# lots of little things need to be initialized...   
def main():

  global configuration
  # I'll grab the necessary information first...
  
  print "loading config"
  # BUG: Do this better?   Is this the right way to engineer this?
  configuration = persist.restore_object("nodeman.cfg")
  
  # get the external IP address...
  # BUG: What if my external IP changes?   (A problem throughout)
  
  vesseldict = nmrequesthandler.initialize(misc.getmyip(),configuration['publickey'],version)

  # Start accept thread...
  myname = start_accept_thread()

  # Start worker thread...
  start_worker_thread(configuration['pollfrequency'])

  # Start advert thread...
  start_advert_thread(vesseldict, myname)

  # Start status thread...
  start_status_thread(vesseldict,configuration['pollfrequency'])


  # we should be all set up now.   

  print "started"
  # BUG: Need to exit all when we're being upgraded
  while True:

    if not is_accept_thread_started():
      print "At ",time.time(),"restarting accept..."
      newname = start_accept_thread(vesseldict)
      # I have just updated the name for the advert thread...
      nmadvertise.myname = newname
        
    if not is_worker_thread_started():
      print "At ",time.time(),"restarting worker..."
      start_worker_thread(configuration['pollfrequency'])

    if should_start_waitable_thread('advert','Advertisement Thread'):
      print "At ",time.time(),"restarting advert..."
      start_advert_thread(vesseldict,myname)

    if should_start_waitable_thread('status','Status Monitoring Thread'):
      print "At ",time.time(),"restarting status..."
      start_status_thread(vesseldict,configuration['pollfrequency'])

    time.sleep(configuration['pollfrequency'])



if __name__ == '__main__':
  main() 
