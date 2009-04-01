"""
Author: Armon Dadgar
Start Date: March 31st, 2009
Description:
  Provides a tool-chain for altering resource files.

"""

# Finds all resource files
import glob

def read_restrictions_file(file):
  """
  <Purpose>
    Reads in the contents of a restrictions file.
    
  <Arguments>
    file: name/path of the file to open
  
  <Returns>
    A string buffer with the contents of the file.  
  """
  # Get the file handle, read mode
  fileh = open(file)
  
  # Read in all the contents
  contents = fileh.read()
  
  # Close the file handle
  fileh.close()
  
  return contents
  
def write_restrictions_file(file, buffer):
  """
  <Purpose>
    Writes in the contents of a restrictions file.
    
  <Arguments>
    file: name/path of the file to open
    buffer: The contents of the restrictions file
  
  <Returns>
    Nothing  
  """
  # Get the file handle, write mode
  fileh = open(file, "w")
  
  # Write in all the buffer
  fileh.write(buffer)
  
  # Close the file handle
  fileh.close()
  

def update_restriction(contents, restriction, restype, val, func=False):
  """
  <Purpose>
    Updates a resource in a restrictions file
  
  <Arguments>
    contents: The contents of the restrictions file
    restriction: The name of the restriction e.g. resource, call
    restype: The type of restriction, e.g. events
    val: Either a new absolute value, or a callback function
    func: If true, this indicates that val is a function. That function will be given a list of the elements on the current line, and is expected
    to return the appropriate val to use.
  
  <Side Effects>
    The restrictions file will be modified
  
  <Returns>
    The contents of the new restrictions file
  """
  # Explode file on the newline
  lines = contents.split("\n")
  
  # Empty buffer for new contents
  newContents = ""
  
  # Check each line if it contains the resource
  for line in lines:
    if restriction in line:
      # Explode on space
      lineContents = line.split(" ")
      
      # Make sure this is the correct resource
      try:
        assert(lineContents[0] == restriction)
        assert(lineContents[1] == restype)
      except AssertionError:
        # Wrong line, continue after appending this line
        newContents += line+"\n"
        continue
        
      # Check if we are using a callback function
      if func:
        userVal = val(lineContents)
      else:
        # Otherwise, this is just the real value
        userVal = val
    
      # Change the value to the string val
      lineContents[2] = str(userVal)
      
      # Re-create the line string, with the modifications
      lineString = ""
      for x in lineContents:
        lineString += x + " "
      lineString = lineString.strip()
      lineString += "\n"
      
      # Append the new line to the buffer
      newContents += lineString
      
    else:
      # Just append this line to the buffer
      newContents += line+"\n"
      
  # Return the modified buffer
  return newContents


def get_all_resource_files():
  """
  <Purpose>
    Returns a list with all the resource files.
  
  <Returns>
    A list object with file names.  
  """
  return glob.glob("resource.v*")
  

def process_restriction_file(file, tasks):
  """
  <Purpose>
    Serves as a useful macro for processing a resource file.
  
  <Argument>
    file: The name of a resource file.
    tasks: A list of tuple objects. Each tuple should contain the following:
    (restriction, restype, val, func). See update_restriction for the meaning of these values.
  
  <Returns>
    Nothing
  """
  # Get the content
  content = read_restrictions_file(file)

  # Create a new buffer to store the changes
  newContent = content
  
  # Run each task against the restrictions file
  for t in tasks:
    (restriction, restype, val, func) = t
    newContent = update_restriction(newContent, restriction, restype, val, func)
  
  # Check if there were any changes
  if content != newContent:
    # Write out the changes
    write_restrictions_file(file, newContent)
    
    
def process_all_files(tasks):
  """
  <Purpose>
    Serves as a useful macro for processing all resource files.
  
  <Arguments>
    tasks: A list of tuple objects. Each tuple should contain the following:
    (restriction, restype, val, func). See update_restriction for the meaning of these values.
  
  <Returns>
    None on success. Otherwise,
    A list of all the failures. They are in the form of tuples: (file, exception)
  """
  # Get all the resource files
  allFiles = get_all_resource_files()
  
  # Stores the name of all files that failed
  failedFiles = []
  
  # Process each one
  for rFile in allFiles:
    try:
      # Process this file
      process_restriction_file(rFile, tasks)
    
    # Log if any files fail
    except Exception, exp:
      failedFiles.append((rFile, exp))
  
  # Return the list of failed files, or None if there were no failures
  if len(failedFiles) == 0:
    return None
  else:  
    return failedFiles


