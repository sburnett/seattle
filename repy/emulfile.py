"""
   Author: Justin Cappos

   Start Date: 27 June 2008

   Description:

   This is a collection of functions, etc. that need to be emulated in order
   to provide the programmer with a reasonable environment.   This is used
   by repy.py to provide a highly restricted (but usable) environment.
"""

import restrictions
import nanny
# needed for listdir and remove
import os 
import idhelper

# needed for locking the fileinfo hash
import threading

# I need to rename file so that the checker doesn't complain...
myfile = file

# PUBLIC
def listdir():
  """
   <Purpose>
      Allows the user program to get a list of files in their area.

   <Arguments>
      None

   <Exceptions>
      This probably shouldn't raise any errors / exceptions so long as the
      node manager isn't buggy.

   <Side Effects>
      None

   <Returns>
      A list of strings (file names)
  """

  restrictions.assertisallowed('listdir')

  return os.listdir('.')
   

# PUBLIC
def removefile(filename):
  """
   <Purpose>
      Allows the user program to remove a file in their area.

   <Arguments>
      filename: the name of the file to remove.   It must not contain 
      characters other than 'a-zA-Z0-9.-_' and cannot be '.' or '..'

   <Exceptions>
      An exception is raised if the file does not exist

   <Side Effects>
      None

   <Returns>
      None
  """

  restrictions.assertisallowed('removefile')

  assert_is_allowed_filename(filename)
  
  # Problem notification thanks to Andrei Borac
  # Handle the case where the file is open via an exception to prevent the user
  # from removing a file to circumvent resource accounting

  fileinfolock.acquire()
  try:
    for filehandle in fileinfo:
      if filename == fileinfo[filehandle]['filename']:
        raise Exception, 'File "'+filename+'" is open with handle "'+filehandle+'"'

    result = os.remove(filename)
  finally:
    fileinfolock.release()

  return result
   




# PUBLIC
def emulated_open(filename, mode="rb"):
  """
   <Purpose>
      Allows the user program to open a file safely. This function is meant
      to resemble the builtin "open".

   <Arguments>
      filename:
         The file that should be operated on.
      mode:
         The mode (see open).

   <Exceptions>
      As with open, this may raise a number of errors. Additionally:

      TypeError if the mode is not a string.
      ValueError if the modestring is invalid.

   <Side Effects>
      Opens a file on disk, using a file descriptor. When opened with "w"
      it will truncate the existing file.

   <Returns>
      A file-like object.
  """

  if type(mode) is not str:
    raise TypeError("Attempted to open file with invalid mode (must be a string).")

  restrictions.assertisallowed('open', filename, mode)

  # We just filter out 'b' / 't' in modestrings because emulated_file opens
  # everything in binary mode for us.

  originalmode = mode

  if 'b' in mode:
    mode = mode.replace('b','')

  if 't' in mode:
    mode = mode.replace('t','')

  # Now we use our very safe, cross-platform open-like function and other
  # file-object methods to emulate ANSI file modes.

  file_object = None
  if mode == "r":
    file_object = emulated_file(filename, "r")

  elif mode == "r+":
    file_object = emulated_file(filename, "rw")

  elif mode == "w" or mode == "w+":
    file_object = emulated_file(filename, "rw", create=True)
    fileinfo[file_object.filehandle]['fobj'].truncate()

  elif mode == "a" or mode == "a+":
    file_object = emulated_file(filename, "rw", create=True)
    file_object.seek(0, os.SEEK_END)


  if file_object is None:
    raise ValueError("Invalid or unsupported mode ('%s') passed to open()." % originalmode)

  return file_object




# This keeps the state for the files (the actual objects, etc.)
fileinfo = {}
fileinfolock = threading.Lock()



# private.   Checks the filename for disallowed characters
def assert_is_allowed_filename(filename):

  # file names must contain *only* these chars
  filenameallowedchars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._-'

  # I should check to see if the filename is allowed.   I'm going to do
  # this here.  
  if type(filename) != str:
    raise TypeError, "filename is not a string!"

  # among other things, this avoids them putting / or \ in the filename
  for char in filename:
    if char not in filenameallowedchars:
      raise TypeError, "filename has disallowed character '"+char+"'"
 
  # Should I do anything more rigorous?   I.e. check for links, etc.?
  if filename == "." or filename == '..':
    raise TypeError, "filename cannot be a directory"




# PUBLIC class.  The user can mess with this...
class emulated_file:
  """
    A safe file-like class that resembles the builtin file class.
    The functions in this file are essentially identical to the builtin file
    class

  """

  # This is an index into the fileinfo table...

  filehandle = None

  # I do not use these.   This is merely for user / API convenience
  mode = None
  name = None
  softspace = 0

  def __init__(self, filename, mode="r", create=False):
    """
     <Purpose>
        Allows the user program to open a file safely.   This function is not
        meant to resemble the builtin "open".

     <Arguments>
        filename:
           The file that should be operated on
        mode:
           The mode:
              "r":  Open the file for reading.
              "rw": Open the file for reading and writing.

              These are the only valid modes accepted by this version of
              open(). Note: files are always opened in "binary" mode.
        create:
           If True, create the file if it doesn't exist already.

     <Exceptions>
        As with open, this may raise a number of errors. Additionally:

        ValueError is raised if this is passed an invalid mode.

     <Side Effects>
        Opens a file on disk, using a file descriptor.

     <Returns>
        A file-like object 
    """

    # Only allow 'r' and 'rw'.

    actual_mode = None
    if mode == "r":
      actual_mode = "rb"
    elif mode == "rw":
      actual_mode = "r+b"

    if actual_mode is None:
      raise ValueError("Valid modes for opening a file in repy are 'r' and 'rw'.")
     
    restrictions.assertisallowed('file.__init__', filename, actual_mode)

    # Here we are checking that we only open a given file once in 'write' mode
    # so that file access is more uniform across platforms. (On Microsoft
    # Windows, for example, writing to the same file from two different file-
    # handles throws an error because of the way Windows (by default) locks
    # files opened for writing.)
    fileinfolock.acquire()

    try:
      # Check the entire fileinfo dictionary for the same file already being
      # open.
      for fileinfokey in fileinfo.keys():

        # If the filename matches this one, raise an exception.
        if os.path.abspath(fileinfo[fileinfokey]['filename']) == \
            os.path.abspath(filename):
          raise ArgumentError(\
              "A file is only allowed to have one open filehandle.")

      assert_is_allowed_filename(filename)

      # If the file doesn't exist and the create flag was passed, create the
      # file first.
      if create and not os.path.exists(filename):
        # Create a file by opening it in write mode and then closing it.
        restrictions.assertisallowed('file.__init__', filename, 'wb')

        created_file = myfile(filename, 'wb')
        created_file.close()

      self.filehandle = idhelper.getuniqueid()

      nanny.tattle_add_item('filesopened', self.filehandle)

      fileinfo[self.filehandle] = {'filename':filename, \
          'mode':actual_mode, 'fobj':myfile(filename, actual_mode)}
      self.name = filename
      self.mode = mode

    finally:
      fileinfolock.release()


  # We are iterable!
  def __iter__(self):
    return self


#
# Do most of the normal file calls by checking them and passing them through
#

  def close(self):
    # prevent TOCTOU race with client changing my filehandle
    myfilehandle = self.filehandle
    restrictions.assertisallowed('file.close')

    # Ignore multiple closes (as file does)
    if myfilehandle not in fileinfo:
      return

    nanny.tattle_remove_item('filesopened',myfilehandle)

    fileinfolock.acquire()
    try:
      returnvalue = fileinfo[myfilehandle]['fobj'].close()

      # delete the filehandle
      del fileinfo[myfilehandle]

    finally:
      fileinfolock.release()

    return returnvalue



  def flush(self):
    # prevent TOCTOU race with client changing my filehandle
    myfilehandle = self.filehandle
    restrictions.assertisallowed('file.flush')

    return fileinfo[myfilehandle]['fobj'].flush()


  def next(self):
    # prevent TOCTOU race with client changing my filehandle
    myfilehandle = self.filehandle
    restrictions.assertisallowed('file.next')

    # wait if it's already over used
    nanny.tattle_quantity('fileread',0)

    readdata = fileinfo[myfilehandle]['fobj'].next()

    nanny.tattle_quantity('fileread', len(readdata))

    return readdata



  def read(self,*args):
    # prevent TOCTOU race with client changing my filehandle
    myfilehandle = self.filehandle
    restrictions.assertisallowed('file.read',*args)

    # wait if it's already over used
    nanny.tattle_quantity('fileread',0)

    readdata = fileinfo[myfilehandle]['fobj'].read(*args)

    nanny.tattle_quantity('fileread',len(readdata))

    return readdata


  def readline(self,*args):
    # prevent TOCTOU race with client changing my filehandle
    myfilehandle = self.filehandle
    restrictions.assertisallowed('file.readline',*args)

    # wait if it's already over used
    nanny.tattle_quantity('fileread',0)

    readdata =  fileinfo[myfilehandle]['fobj'].readline(*args)

    nanny.tattle_quantity('fileread',len(readdata))

    return readdata


  def readlines(self,*args):
    # prevent TOCTOU race with client changing my filehandle
    myfilehandle = self.filehandle
    restrictions.assertisallowed('file.readlines',*args)

    # wait if it's already over used
    nanny.tattle_quantity('fileread',0)

    readlist = fileinfo[myfilehandle]['fobj'].readlines(*args)
    readamt = 0
    for readitem in readlist:
      readamt = readamt + len(str(readitem))

    nanny.tattle_quantity('fileread',readamt)

    return readlist


  def seek(self,*args):
    # prevent TOCTOU race with client changing my filehandle
    myfilehandle = self.filehandle
    restrictions.assertisallowed('file.seek',*args)

    return fileinfo[myfilehandle]['fobj'].seek(*args)


  def write(self,writeitem):
    # prevent TOCTOU race with client changing my filehandle
    myfilehandle = self.filehandle
    restrictions.assertisallowed('file.write',writeitem)

    # wait if it's already over used
    nanny.tattle_quantity('filewrite',0)

    retval = fileinfo[myfilehandle]['fobj'].write(writeitem)

    writeamt = len(str(writeitem))
    nanny.tattle_quantity('filewrite',writeamt)

    return retval


  def writelines(self,writelist):
    # prevent TOCTOU race with client changing my filehandle
    myfilehandle = self.filehandle
    restrictions.assertisallowed('file.writelines',writelist)

    # wait if it's already over used
    nanny.tattle_quantity('filewrite',0)

    retval = fileinfo[myfilehandle]['fobj'].writelines(writelist)
    writeamt = 0
    for writeitem in writelist:
      writeamt = writeamt + len(str(writeitem))

    nanny.tattle_quantity('filewrite',writeamt)
    return retval


# End of emulated_file class

