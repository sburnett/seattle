"""
<Program Name>
  update_crontab_entry.py

<Started>
  October 2, 2009

<Author>
  Zachary Boka

<Purpose>
  Modifies the current crontab entry to reflect the new "@reboot" directive
  which will use cron to start seattle only upon machine boot.  If there is
  currently no entry for seattle in the crontab, then this function does not add
  nor modify the crontab.
"""
# Python modules
import subprocess
import os
import tempfile

# Seattle modules
import nonportable
import servicelogger


def modify_seattle_crontab_entry():
  """
  <Purpose>
    Replaces the current seattle crontab entry, if it exists, with the updated
    entry which uses the directive @reboot to specify that cron should only
    start seattle at machine boot.

  <Arguments>
    None.

  <Exceptions>
    OSError if cron is not installed on this system?
    IOError if there is a problem creating or writing to the temporary file?

  <Side Effects>
    Modifies the seattle crontab entry, should it exist.

  <Returns>
    None.
  """

  try:
    crontab_contents = subprocess.Popen(["crontab","-l"],stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)
    crontab_contents_stdout = crontab_contents.stdout
  except Exception,e:
    # User does not have access to crontab, so do nothing and return.
    return
  else:
    # Get the service vessel where any cron errors or output for seattle will
    # be written.
    service_vessel = servicelogger.get_servicevessel()

    # Create the replacement crontab entry.
    seattle_files_dir = os.path.realpath(".")
    cron_line_entry = '@reboot if [ -e "' + seattle_files_dir + os.sep \
        + 'start_seattle.sh" ]; then "' + seattle_files_dir + os.sep \
        + 'start_seattle.sh" >> "' + seattle_files_dir + os.sep \
        + service_vessel + '/cronlog.txt" 2>&1; else crontab -l | ' \
        + 'sed \'/start_seattle.sh/d\' > /tmp/seattle_crontab_removal && ' \
        + 'crontab /tmp/seattle_crontab_removal && ' \
        + 'rm /tmp/seattle_crontab_removal; fi' + os.linesep


    # Generate a temporary crontab file, and only add the new seattle crontab
    # entry if there is currently an outdated seattle crontab entry.
    temp_crontab_file = tempfile.NamedTemporaryFile()
    outdated_seattle_entry_existed = False
    for line in crontab_contents_stdout:
      if "start_seattle.sh" in line:
        line = cron_line_entry
        outdated_seattle_entry_existed = True
      temp_crontab_file.write(line)
    temp_crontab_file.flush()
    

    # If there was no outdated seattle entry, close the temporary file and
    # return.
    if not outdated_seattle_entry_existed:
      temp_crontab_file.close()
      return


    # Now, replace the crontab with that temp file and remove(close) the
    # tempfile.
    replace_crontab = subprocess.Popen(["crontab",temp_crontab_file.name],
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
    replace_crontab.wait()                                    
    temp_crontab_file.close()
    



def main():
  """
  <Purpose>
    Test the operating system.  If this a Linux or Darwin machine, change the
    seattle crontab entry if it exists.

  <Arguments>
    None.

  <Exceptions>
    None.

  <Side Effects>
    Modifies the seattle crontab entry if it exists.

  <Returns>
    None.
  """

  if not nonportable.ostype == "Linux" and not nonportable.ostype == "Darwin":
    return
  else:
    modify_seattle_crontab_entry()




if __name__ == "__main__":
  main()
