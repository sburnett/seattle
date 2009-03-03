import os
import repyhelper

#Given a filename, return the corresponding translation filename
def get_translation_filename(filename):
  return repyhelper._get_module_name(filename) + '.py'

#Given a list of python files, return a list of the corresponding translated filenames
def get_translation_filenames(filenames):
  return map(get_translation_filename, filenames)

def cleanup_files(files):
  """
    Remove the files list in files, to ensure that fresh translations are used
    between unit tests
    
  """
  for f in files:
    if os.path.isfile(f):
      try:
        os.remove(f)
      except (OSError, IOError):
        pass

