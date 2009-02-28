"""
<Program>
  servicelogger.py

<Date Started>
  January 24th, 2008

<Author>
  Brent Couvrette
  couvb@cs.washington.edu

<Purpose>
  Module abstracting away service logging.  Other modules simply have to call
  log with the name of the log file they wish to write to, and the
  servicelogger will write their message with time and pid stamps to the
  service vessel.  init must be called before log.
"""
import logging

import time

import os

logfile = None
servicevessel = None

class ServiceLogError(Exception):
  pass


def init(logname, cfgdir='.'):
  """
  <Purpose>
    Sets up the service logger to use the given logname, and the nodeman.cfg
    is in the given directory.
    
  <Arguments>
    logname - The name of the log file, as well as the name of the process lock
              to be used in the event of multi process locking
    cfgdir - The directory containing nodeman.cfg, by default it is the current
             directory
             
  <Exceptions>
    Exception if there is a problem reading from cfgdir/nodeman.cfg
    
  <Side Effects>
    All future calls to log will log to the given logfile.
    
  <Returns>
    None
  """

  global logfile
  global servicevessel

  # We don't use persist anymore because persist will fail if multiple 
  # processes try to read the file at the same time, which is possible.
  readfileobj = open(cfgdir + '/nodeman.cfg')
  readdata = readfileobj.read()
  readfileobj.close()

  servicevessel = (eval(readdata))['service_vessel']
  logfile = logging.circular_logger(cfgdir + '/' + servicevessel + '/' + 
      logname, use_nanny=False)


def multi_process_log(message, logname, cfgdir='.'):
  """
  <Purpose>
    Logs the given message to a log.  Does some trickery to make sure there
    no more than 10 logs are ever there.
    
  <Arguments>
    message - The message that should be written to the log.
    logname - The name to be used for the logfile.
  
  <Exceptions>
    Exception if there is a problem reading from cfgdir/nodeman.cfg or writing
    to the circular log.
      
  <Side Effects>
    The given message might be written to the log.
    
  <Returns>
    None
  """
  global servicevessel
  
  if servicevessel == None:
    # We don't use persist anymore because persist will fail if multiple 
    # processes try to read the file at the same time, which is possible.
    readfileobj = open(cfgdir + '/nodeman.cfg')
    readdata = readfileobj.read()
    readfileobj.close()
    servicevessel = (eval(readdata))['service_vessel']
    
  logcount = 0
  for servicefile in os.listdir(cfgdir + '/' + servicevessel):
    if servicefile.endswith('.old'):
      # Count all the log files.  There is always a .old for every log?
      logcount = logcount + 1
      
  if logcount >= 10:
    # If there are 10 or more logfiles already present, we don't want to create
    # another.  To deal with the possibility of a time of check / time of use
    # vulnerability, I will recheck this after I write the file, and deal with
    # it then.  For simplicity we will just return in this case.  We might do
    # something fancier here later.
    return
  else:
    logfile = logging.circular_logger(cfgdir + '/' + servicevessel + '/' + logname)
    logfile.write(str(time.time()) + ':PID-' +str(os.getpid()) + ':' +
      str(message) + '\n')
    logfile.close()
    
    # Redo the check to make sure there weren't huge amounts of logs created
    # after we checked.  If so, lets delete ourselves so we don't contribute
    # to the mess.
    logcount = 0
    for servicefile in os.listdir(cfgdir + '/' + servicevessel):
      if servicefile.endswith('.old'):
        # Count all the log files.  There is always a .old for every log?
        logcount = logcount + 1
      
    if logcount >= 10:
      # Make sure we try to remove both the .old and .new files.
      try:
        # We will try our best to remove the file, but if it fails, we can't
        # do much about it.
        os.remove(cfgdir + '/' + servicevessel + '/' + logname + '.old')
      except Exception:
        pass
        
      try:
        # We will try our best to remove the file, but if it fails, we can't
        # do much about it.
        os.remove(cfgdir + '/' + servicevessel + '/' + logname + '.new')
      except Exception:
        pass


def log(message):
  """
  <Purpose>
    Logs the given text to the given log file inside the service directory.
    
  <Argument>
    message - The message to log.
    
  <Exceptions>
    ServiceLogError if init has not been called.
    Exception if writing to the log fails somehow.
    
  <Side Effects>
    The given message is written to the circular log buffer.
    
  <Returns>
    None
  """

  if logfile == None:
    # If we don't have a current log file, lets raise an exception
    raise ServiceLogError("init needs to be called before using the service log")

  logfile.write(str(time.time()) + ':PID-' + str(os.getpid()) + 
    ':' + str(message) + '\n')
