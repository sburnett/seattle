"""
<Program>
  measuredisk_linux.py

<Author>
  Brent Couvrette

<Started>
  January 17, 2008

<Purpose>
  This script will attempt to measure disk read rate on linux.  Current plan
  being attempted:
    Time how long it takes to write 16MB, use that value for both read and
    write rate.
"""

import os
import time
import subprocess

def measure_write(num_bytes):
  """
  <Purpose>
    Attempts to measure the disk write rate by writing num_bytes bytes to a
    temp file, timing how long it took, and dividing num_bytes by the time
    to get the write rate.

  <Arguments>
    num_bytes - The number of bytes that should be written to determine the
                write rate.

  <Side Effects>
    Creates a file of size num_bytes.

  <Exceptions>
    Exceptions could be thrown if there is a problem opening/writing the file.

  <Return>
    A tuple (rate, fn) where rate is the measured write rate, and fn is the 
    name of the file created.  It is up to the caller to ensure that this 
    file is deleted.  We do not delete it here because it will likely be 
    useful in doing the read rate measurments.
  """
  # Create the filename based on the pid to make sure we don't accidentally
  # overwrite something.  I don't use mkstemp because I'm not sure those
  # files are necesarily written to disk.
  pid = os.getpid()
  junk_fn = 'rate_measure.'+str(pid)
  
  junk_file = open(junk_fn, 'w')

  # Time how long it takes to write out num_bytes.  Does writing all of one
  # character affect the time?  Does flush make sure all disk writing happens
  # before it returns?
  start_time = time.time()
  junk_file.write(' ' * num_bytes)
  junk_file.flush()
  subprocess.call('sync')
  end_time = time.time()
  junk_file.close()

  return (num_bytes/(end_time - start_time), junk_fn)


def measure_read(num_bytes, junk_fn):
  """
  <Purpose>
    Attempts to measure the disk read rate by reading num_bytes bytes from a
    temp file, timing how long it took, and dividing num_bytes by the time
    to get the read rate.

  <Arguments>
    num_bytes - The number of bytes that should be read to determine the
                read rate.

  <Side Effects>
    None

  <Exceptions>
    Exceptions could be thrown if there is a problem opening/reading the file.

  <Return>
    A tuple (rate, num_bytes) where rate is the measured read rate, and 
    num_bytes is the number of bytes actually read.  It will be no more than
    what was actually asked for, but it could be less if the given file was 
    too short.  The read rate will have been calculated using the returned
    num_bytes.
  """
  junk_file = open(junk_fn, 'r')

  # Time how long it takes to read in num_bytes.
  start_time = time.time()
  junk_data = junk_file.read(num_bytes)
  end_time = time.time()
  junk_file.close()

  num_bytes = len(junk_data)

  return (num_bytes/(end_time - start_time), num_bytes)


def main():
  write_rate, junk_fn = measure_write(16*1024*1024)
  os.remove(junk_fn)
  print 'resource filewrite ' + str(int(write_rate))
  print 'resource fileread ' + str(int(write_rate))
  
  
if __name__ == '__main__':
  main()
