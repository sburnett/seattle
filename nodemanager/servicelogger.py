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
from repyportability import *

import logging

import persist

logfile = None

class ServiceLogError(Exception):
  pass

def init(filename):
  """
  <Purpose>
    Sets up the service logger to log to the given file.
  <Arguments>
    filename - the name of the log file to write to.i
  """
  global logfile

  configuration = persist.restore_object("nodeman.cfg")
  logfile = logging.circular_logger(configuration['service_vessel'] + '/' + filename)



def log(message):
  """
  <Purpose>
    Logs the given text to the given log file inside the service directory.
  <Argument>
    message - The message to log.
  """

  if logfile == None:
    # If we don't have a current log file, lets raise an exception
    raise ServiceLogError("init needs to be called before using the service log")

  logfile.write(str(time.time()) + ':PID-' + str(os.getpid()) + 
    ':' + str(message) + '\n')
