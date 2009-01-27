"""
<Program Name>
  build_installers.py

<Started>
  November 18, 2008

<Author>
  Carter Butaud

<Purpose>
  Provides various methods useful for building and customizing
  the installers, including methods to build an entire installer,
  to build all the installers, and to add files to existing
  installers.
"""

import os
import sys
import shutil
import subprocess

PROGRAM_NAME = "build_installers"

def append_to_zip(zip_file, folder_to_append, zip_file_dir):
    """
    <Purpose>
      Recursively adds all files in a given folder to a given zip file.

    <Arguments>
      zip_file:
        The file to which the files in the new folder will be appended.
      folder_to_append:
        The folder containing all the files to be added to the zip file.
      zip_file_dir:
        The location in the zip file to which the files should be added.

    <Exceptions>
      IOError on bad filepaths.
    
    <Side Effects>
      None.

    <Returns>
      None.
    """
    if not os.path.exists(zip_file):
        raise IOError("File not found: " + zip_file)
    if not os.path.exists(folder_to_append):
        raise IOError("File not found: " + folder_to_append)
    orig_dir = os.getcwd()
    temp_dir = "/tmp/" + PROGRAM_NAME + str(os.getpid())
    os.mkdir(temp_dir)
    append_path = temp_dir + "/" + zip_file_dir
    shutil.copytree(folder_to_append, append_path)
    shutil.copy2(zip_file, temp_dir)
    # Navigate to the temp folder and back to work around zip's
    # idiosyncracies.
    os.chdir(temp_dir)
    zip_file_name = zip_file.split("/")[-1]
    p = subprocess.Popen("zip -r " + zip_file_name + " " + 
                         zip_file_dir, shell=True)
    p.wait()
    os.chdir(orig_dir)
    shutil.copy2(temp_dir + "/" + zip_file_name, zip_file)
    shutil.rmtree(temp_dir)

def append_to_tar(tarball, folder_to_append, tarball_dir):
    """
    <Purpose>
      Recursively adds all files in a given folder to a given tarball.

    <Arguments>
      tarball:
        The tarball to which the files in the new folder will be appended.
      folder_to_append:
        The folder containing all the files to be added to the tarball.
      tarball_dir:
        The location in the tarball to which the files should be added.

    <Exceptions>
      IOError on bad filepaths.

    <Side Effects>
      None.

    <Returns>
      None.
    """
    if not os.path.exists(tarball):
        raise IOError("File not found: " + tarball)
    if not os.path.exists(folder_to_append):
        raise IOError("File not found: " + folder_to_append)
    orig_dir = os.getcwd()
    # Create a unique temp directory
    temp_dir = "/tmp/" + PROGRAM_NAME + str(os.getpid())
    if not os.path.exists(temp_dir):
        os.mkdir(temp_dir)
    append_path = temp_dir + "/" + tarball_dir
    if os.path.exists(append_path):
        shutil.rmtree(append_path)
    os.mkdir(append_path)
    # Copy the files to be appended over
    command = "cp -r " + folder_to_append + "/* " + append_path
    p = subprocess.Popen(command, shell=True)
    p.wait()
    # Copy the tarball over
    shutil.copy2(tarball, temp_dir)
    # Navigate to the temp directory to deal with tar's idiosyncrasies.
    os.chdir(temp_dir)
    # Unzip the tarball so we can append files to it.
    zipped_tarball_name = tarball.split("/")[-1]
    command = "gzip -d " + zipped_tarball_name
    p = subprocess.Popen(command, shell=True)
    p.wait()
    # Append the appropriate files to the tarball.
    base_tarball_name = ""
    if zipped_tarball_name.endswith(".tar.gz"):
        # If the original file was "*.tar.gz"...
        base_tarball_name = zipped_tarball_name[:-6]
    else:
        # Assume the original file was "*.tgz".
        base_tarball_name = zipped_tarball_name[:-4]
    command = "tar -rf " + base_tarball_name + ".tar " + tarball_dir
    p = subprocess.Popen(command, shell=True)
    p.wait()
    # Zip up the tarball, make sure it is named appropriately, and copy
    # it back to its original location.
    command = "gzip " + base_tarball_name + ".tar"
    p = subprocess.Popen(command, shell=True)
    p.wait()
    os.chdir(orig_dir)
    shutil.copy2(temp_dir + "/" + base_tarball_name + ".tar.gz", tarball)
   


def main():
    if len(sys.argv) < 4:
        print "usage: python build_installers.py tarball folder_to_append tarball_dir"
    else:
        append_to_tar(sys.argv[1], sys.argv[2], sys.argv[3])

if __name__ == "__main__":
    main()
