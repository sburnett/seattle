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

# Used to determine the os type and for getruntime.
import nonportable

# Get the ctypes stuff so we can call libc.sync() instead of using subprocces.
# We want to do all the importing and such here so that it doesn't muck with
# the timing.  These things don't seem to be available on Windows, so we will
# only import them where we need them (Linux)
if nonportable.osrealtype == 'Linux':
  import ctypes
  import ctypes.util
  libc = ctypes.CDLL(ctypes.util.find_library("c"))


def measure_write(write_file_obj, num_bytes, use_sync=False):
  """
  <Purpose>
    Attempts to measure the disk write rate by writing num_bytes bytes to a
    temp file, timing how long it took, and dividing num_bytes by the time
    to get the write rate.

  <Arguments>
    write_file - The file to be written to.  This should be an already opened
                 file handle that was opened with write access.
    num_bytes - The number of bytes that should be written to determine the
                write rate.
    use_sync - Set to True if sync should be used to make sure the data is
               actually written to disk.  Should not be set to True on
               Windows because sync does not exist there.  Defaults to False.

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
  
  # Time how long it takes to write out num_bytes.  Does writing all of one
  # character affect the time?  Does flush make sure all disk writing happens
  # before it returns?
  start_time = nonportable.getruntime()
  write_file_obj.write(' ' * num_bytes)
  write_file_obj.flush()
  if use_sync:
    # Only use sync if it is requested.
    libc.sync()

  end_time = nonportable.getruntime()

  return num_bytes/(end_time - start_time)


def measure_read(read_file_obj, num_bytes):
  """
  <Purpose>
    Attempts to measure the disk read rate by reading num_bytes bytes from a
    temp file, timing how long it took, and dividing num_bytes by the time
    to get the read rate.  Note that at this time, read rate is far too fast
    because it reads what was just written.  It should be ok to just take the
    value given by the write test and use it for both read and write rate.

  <Arguments>
    read_file_obj - The file object that is to be read from for the read test.
                    This file object is not closed by this function.
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

  # Time how long it takes to read in num_bytes.
  start_time = nonportable.getruntime()
  junk_data = read_file_obj.read(num_bytes)
  end_time = nonportable.getruntime()

  num_bytes = len(junk_data)

  return (num_bytes/(end_time - start_time), num_bytes)


def main():
  # Create the filename based on the pid to make sure we don't accidentally
  # overwrite something.  I don't use mkstemp because I'm not sure those
  # files are necesarily written to disk.
  pid = os.getpid()
  write_file_obj = open('rate_measure.'+str(pid), 'w')
  try:
    # On linux sync needs to be run, otherwise it returns values an order of
    # magnitude too large.
    if nonportable.osrealtype == 'Linux':
      write_rate = measure_write(write_file_obj, 16*1024*1024, True)
    else:
      write_rate = measure_write(write_file_obj, 16*1024)

    write_file_obj.close()
  finally:
    os.remove(write_file_obj.name)

  print 'resource filewrite ' + str(int(write_rate))
  # Currently the read rate measurement is ridiculusly high, likely because
  # we are reading something that we just wrote.  Because it would be 
  # non-trivial to get an accurate read rate, we feel it is safe enough to
  # assume that the read and write rates are the same, so we just print out
  # the write_rate here as well.
  print 'resource fileread ' + str(int(write_rate))
  

  
if __name__ == '__main__':
  main()
