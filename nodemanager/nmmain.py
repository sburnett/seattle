""" 
Author: Justin Cappos
  Modified by Brent Couvrette to make use of circular logging.


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

# The circular logger makes nanny calls.  Because this is not being called
# from repy, what would the nanny do?  Here we truncate the nanny calls with
# repyportability.  Do we want to truncate them, or should the nodemanager's
# log be rate limited as well?  Would an attacker plausibly be able to say,
# crash a thread so repeatedly that the logging makes a noticable impact on 
# the system? - Brent Couvrette
from repyportability import *

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

import runonce

# for harshexit...
import nonportable

# import logging so we can log to a circular log - Brent Couvrette
import logging

import traceback


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

# The circular log file that things will be written to when log is called.
# log will automatically set this up the first time it is called. 
# - Brent Couvrette
log_file = None

# BUG: what if the data on disk is corrupt?   How do I recover?   What is the
# "right thing"?   I could run nminit again...   Is this the "right thing"?

version = "0.1b"

# Our settings
configuration = {}

def log(text):
  """
  <Purpose>
    Logs the given text to the circular log buffer.

  <Author>
    Brent Couvrette - couvb@cs.washington.edu
  """
  global log_file
  
  if log_file is None:
    # If log_file is not a circular_logger, it should be created.
    # Do we want the location of the log file hardcoded here or as an argument?
    log_file = logging.circular_logger('v2/nodemanager.log')

  # I append a \n because I feel it is best to assume that the given text did
  # not do so.  This way if we are wrong, there is just an extra newline, but
  # the log is still readable.  If we left off the newline and we are wrong,
  # we are left with a hard to read log, which makes it much less useful.
  log_file.write(str(text)+'\n')



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
      acceptthread = nmconnectionmanager.AcceptThread(misc.getmyip(), 
          configuration['ports'])
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
  

def handle_exception(frame, event, arg):
  """
  <Author>
    Brent Couvrette
    couvb@cs.washington.edu
  <Purpose>
    This function is made to be used as an argument to settrace, and it will
    write exception tracebacks to the log, and ignore all other events.
  
  <Arguments>
    frame - The current stack frame.  Not used here.
    event - String identifying which event is being thrown.  We only care to
            look for 'exception' events.  See the python documentation for 
            details on other possible values.
    arg - The value of arg depends on the type of event.  In the case of the
          exception event, it should be a tuple of the form (exception, value,
          traceback).
  <Return>
    None when we find an exception so we do as little tracing as possible.  
    Otherwise we must return this function so that it will get called in the
    future and catch the exception
  """
  if event.find('exception') != -1:
    exceptionstring = "[ERROR]:"
    for line in traceback.format_exception(arg[0], arg[1], arg[2]):
      # Combine the traceback into all one string
      exceptionstring = exceptionstring + line

    log(exceptionstring)
    return None
  else:
    return handle_exception
    


# lots of little things need to be initialized...   
def main():

  global configuration


  # ensure that only one instance is running at a time...
  gotlock = runonce.getprocesslock("seattlenodemanager")
  if gotlock == True:
    # I got the lock.   All is well...
    pass
  else:
    if gotlock:
      log("[ERROR]:Another node manager process (pid: " + str(gotlock) + 
          ") is running")
    else:
      log("[ERROR]:Another node manager process is running")
    return

  
  # I'll grab the necessary information first...
  log("[INFO]:Loading config")
  # BUG: Do this better?   Is this the right way to engineer this?
  configuration = persist.restore_object("nodeman.cfg")
  
  # get the external IP address...
  # BUG: What if my external IP changes?   (A problem throughout)
  
  vesseldict = nmrequesthandler.initialize(misc.getmyip(),configuration['publickey'],version)

  # Set the trace function to all the threads to handle_exception here that
  # will log exceptions from all of our threads.  Note:
  # "The settrace() function is intended only for implementing debuggers, 
  # profilers, coverage tools and the like. Its behavior is part of the 
  # implementation platform, rather than part of the language definition, and
  # thus may not be available in all Python implementations." - taken directly
  # from the python documentation.  Is this ok here?
  threading.settrace(handle_exception)

  # Start accept thread...
  myname = start_accept_thread()

  # Start worker thread...
  start_worker_thread(configuration['pollfrequency'])

  # Start advert thread...
  start_advert_thread(vesseldict, myname)

  # Start status thread...
  start_status_thread(vesseldict,configuration['pollfrequency'])


  # we should be all set up now.   

  log("[INFO]:Started")
  # BUG: Need to exit all when we're being upgraded
  while True:

    if not is_accept_thread_started():
      log("[WARN]:At " + str(time.time()) + " restarting accept...")
      newname = start_accept_thread(vesseldict)
      # I have just updated the name for the advert thread...
      nmadvertise.myname = newname
        
    if not is_worker_thread_started():
      log("[WARN]:At " + str(time.time()) + " restarting worker...")
      start_worker_thread(configuration['pollfrequency'])

    if should_start_waitable_thread('advert','Advertisement Thread'):
      log("[WARN]:At " + str(time.time()) + " restarting advert...")
      start_advert_thread(vesseldict,myname)

    if should_start_waitable_thread('status','Status Monitoring Thread'):
      log("[WARN]:At " + str(time.time()) + " restarting status...")
      start_status_thread(vesseldict,configuration['pollfrequency'])

    if not runonce.stillhaveprocesslock("seattlenodemanager"):
      log("[ERROR]:The node manager lost the process lock...")
      nonportable.harshexit(55)

    time.sleep(configuration['pollfrequency'])



if __name__ == '__main__':
  main() 
