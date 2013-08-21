"""
<Program Name>
  deploy_helper.py

<Started>
  May 2009

<Author>
  n2k8000@u.washington.edu
  Konstantin Pik

<Purpose>
  File has helper methods to be used across all the deploy_* libraries.
"""

import subprocess
import time

# Assorted helper functions that don't really go anywhere else

def summarize_all_blocks(text):
  """
  <Purpose>
    If new patterns need to be added to be summarized (aka they're spamming 
    the logs, they'll go here)

  <Arguments>
    text:
      the text that shall be summarized, typically the contents of the log file.

  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    String. Returns text but with all the changes.
  """
  
  
  
  
  text = summarize_block(['Traceback', 'line 151', 'line 89', 'line 222', 
      'line 190', 'line 325', 'line 856', 'line 728', 'line 695', 
      'line 663', 'Temporary failure in name resolution'], text)
      
  """
  1251419423.49:PID-11142:Traceback (most recent call last):
  File "softwareupdater.py", line 151, in safe_download
  File "/vservers/.vref/planetlab-f8-i386/usr/lib/python2.5/urllib.py", line 89, in urlretrieve
  File "/vservers/.vref/planetlab-f8-i386/usr/lib/python2.5/urllib.py", line 222, in retrieve
  File "/vservers/.vref/planetlab-f8-i386/usr/lib/python2.5/urllib.py", line 190, in open
  File "/vservers/.vref/planetlab-f8-i386/usr/lib/python2.5/urllib.py", line 325, in open_http
  File "/vservers/.vref/planetlab-f8-i386/usr/lib/python2.5/httplib.py", line 856, in endheaders
  File "/vservers/.vref/planetlab-f8-i386/usr/lib/python2.5/httplib.py", line 728, in _send_output
  File "/vservers/.vref/planetlab-f8-i386/usr/lib/python2.5/httplib.py", line 695, in send
  File "/vservers/.vref/planetlab-f8-i386/usr/lib/python2.5/httplib.py", line 663, in connect
  IOError: [Errno socket error] (-3, 'Temporary failure in name resolution')
  """
  
  text = summarize_block(["['Timestamps match']"], text)
  text = summarize_block(["['Expired signature']"], text)
  
  text = summarize_block(['Traceback', 'line 75', 'line 49', 'ValueError'], text)
  
  """
  1251205775.07:PID-14482:Traceback (most recent call last):
  File "/home/uw_seattle/seattle_repy/nmrequesthandler.py", line 75, in handle_request
  File "nodemanager.repyhelpercache/session_repy.py", line 49, in session_recvmessage
  ValueError: Bad message size
  """
  
  text = summarize_block(['restarting advert'], text)
  
  text = summarize_block(['[do_rsync] New metainfo not signed correctly. Not updating.'], text)
  
  
  text = summarize_block(['[safe_download] Failed to download http://seattle.cs.washington.edu/couvb/updatesite/0.1/metainfo'], text)
  
  
  text = summarize_block(["The metainfo indicates no update is needed: ['Timestamps match'"], text)
  """
  
  """
  text = summarize_block(['Traceback', 'line 5942', 'line 5823', 'openDHT announce error: Socket closed'], text)
  text = summarize_block(['Traceback', 'line 5942', 'line 5823', "openDHT announce error: (111, 'Connection refused'"], text)
  text = summarize_block(['Traceback', 'line 5942', 'line 5823', 'openDHT announce error: timed out'], text)
  text = summarize_block(['Traceback', 'line 5942', 'line 5823', 'centralized announce error: timed out'], text)
  text = summarize_block(['Traceback', 'line 5942', 'line 5823', "centralized announce error: (111, 'Connection refused')"], text)
  text = summarize_block(['Traceback', 'line 5942', 'line 5823', "centralized announce error: Socket Timeout"], text)
  text = summarize_block(['Traceback', 'line 5942', 'line 5823', "centralized announce error: (-2, 'Name or service not known')"], text)



  """
  1249514361.81:PID-11141:Traceback (most recent call last):
  File "/home/uw_seattle/seattle_repy/nmadvertise.py", line 5942, in run
  File "/home/uw_seattle/seattle_repy/nmadvertise.py", line 5823, in advertise_announce
  AdvertiseError: openDHT announce error: (111, 'Connection refused')
  """


  text = summarize_block(['Traceback', 'line 92', 'line 217', 'line 260',
      'line 215', "NameError: global name 'sha_hash' is not defined"], text)
  """
  1252386102.32:PID-6552:Traceback (most recent call last):
  File "/home/uw_seattle/seattle_repy/nmrequesthandler.py", line 92, in handle_request
  File "/home/uw_seattle/seattle_repy/nmrequesthandler.py", line 217, in process_API_call
  File "/home/uw_seattle/seattle_repy/nmrequesthandler.py", line 260, in ensure_is_correctly_signed
  File "nodemanager.repyhelpercache/signeddata_repy.py", line 215, in signeddata_issignedcorrectly
  NameError: global name 'sha_hash' is not defined
  """

  
  text = summarize_block(['[fresh_software_updater] Fresh software updater started'], text)
  
  text = summarize_block(['Something is wrong with the metainfo'], text)
  
  text = summarize_block(['Traceback', 'line 151', 'line 89', "line 222",
      'line 190', 'line 325', 'line 856', 'line 728', 'line 695', 'line 679', 
      'IOError: [Errno socket error] timed out'], text)
      
  """
  1252011627.59:PID-7346:Traceback (most recent call last):
  File "softwareupdater.py", line 151, in safe_download
  File "/vservers/.vref/planetlab-f8-i386/usr/lib/python2.5/urllib.py", line 89, in urlretrieve
  File "/vservers/.vref/planetlab-f8-i386/usr/lib/python2.5/urllib.py", line 222, in retrieve
  File "/vservers/.vref/planetlab-f8-i386/usr/lib/python2.5/urllib.py", line 190, in open
  File "/vservers/.vref/planetlab-f8-i386/usr/lib/python2.5/urllib.py", line 325, in open_http
  File "/vservers/.vref/planetlab-f8-i386/usr/lib/python2.5/httplib.py", line 856, in endheaders
  File "/vservers/.vref/planetlab-f8-i386/usr/lib/python2.5/httplib.py", line 728, in _send_output
  File "/vservers/.vref/planetlab-f8-i386/usr/lib/python2.5/httplib.py", line 695, in send
  File "/vservers/.vref/planetlab-f8-i386/usr/lib/python2.5/httplib.py", line 679, in connect
  IOError: [Errno socket error] timed out
  """
  
  
  text = summarize_block(['Another software updater old process (pid: '], text)
  text = summarize_block(['Loading config', 'Traceback', 'line 491', 'line 419', 'KeyError'], text)
  text = summarize_block([':need more than 1 value to unpack'], text)
  
  text = summarize_block(['Another node manager process'], text)
  """
  710:[ERROR]:Another node manager process (pid: 11141) is running
  """
  
  text = summarize_block(['node manager is alive'], text)
  
  
  # the below are fixes if the same file is processed multiple times.
  text = summarize_block(['_____', '', '______'], text, False)
  
  text = summarize_block(['Replaced 0 in', '', '___'], text, False)
  
  text = summarize_block(['_____', 'Replaced 0 in', '', '___'], text, False)
  
  text = trim_newlines(text)
  
  text = trim_newlines(text)
  
  return text



def trim_newlines(text):
  """
  <Purpose>
    Replaces \n\n\ns with single \n repeatedly.

  <Arguments>
    text:
      the text to replace.

  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    String. Returns text but with all the changes.
  """
  
  while text != text.replace('\n\n\n', '\n'):
    text = text.replace('\n\n\n', '\n')
    time.sleep(.1)
  text = text.replace('\n\n\n', '\n')
  return text


def summarize_block(pattern_array, text, log = True):
  """
  <Purpose>
    The purpose is to summarize a file that has multiple similar entries 
    into something concise

  <Arguments>
    pattern_array: 
      array of strings.  The array is a pattern to look for, where each element corresponds to
      what the (n+1)th line should look like. e.g.:
        
          ['Traceback', 'line 1234', 'line 3333', 'KeyError']
          
      will look for 'Traceback' on a line, once it finds it it will look for 'line 1234' on the 
      following line and then 'line 3333' on the following line, and 'KeyError' on the next line.
      If it is found the "counter" for instances of this pattern will be increased, and those lines 
      will be removed from the argument text
    text:
      This is the text which will be searched, line by line for the pattern

  <Exceptions>
    None.

  <Side Effects>
    Careless pattern-making can cause unwanted truncation of the text

  <Returns>
    String.  The original text, but with the truncation and changes noted.
  """
  
  # the number of current matches/replacements made
  number_of_matches = 0
  
  # flag for whether we matched something or not
  matched_flag = False
  
  # conver to array as we're going to enumerate through it by line #s
  text_array = text.splitlines()
  
  # will hold a sample of what was actually replaced and what matched the pattern
  sample_replace = []
  
  
  for each_index in range(len(text_array)):
  
    # grab each lien from the text array
    each_line = text_array[each_index]
    
    # we found the first pattern
    if pattern_array[0] in each_line:
      if each_index >= 2 and not text_array[each_index - 1].startswith('Replaced ') and not text_array[each_index - 2].startswith('___'):
        matched_flag = True
      
        # do we have enough lines to match to the pattern?
        if len(pattern_array) - 1 + each_index < len(text_array):
          
          for i in range(len(pattern_array)):
            # try to match the other patterns now

            if matched_flag:

              if len(text_array) > each_index + i:
                next_line = text_array[each_index + i]
              else:
                temp = '\n'.join(text_array)
                
                temp = trim_newlines(temp)
                
                if number_of_matches > 0 and log:
                  temp =  temp + '\n______________________________\n'+\
                      'Replaced '+str(number_of_matches)+' instances of the following pattern: \n'+\
                      '\n'.join(sample_replace)+'\n'+\
                      '______________________________\n'
                return temp
                

              if pattern_array[i] in next_line:
                if pattern_array[i] == '' and next_line != '':
                  matched_flag = False
                else:
                  matched_flag = True
              else:
                matched_flag = False

            
          if matched_flag:
            number_of_matches += 1
            # we matched all the flags, time to replace by grabbing n indexes
            # and replacing them
            
            # do we have a sample of what we replaced?
            if not sample_replace:
              sample_replace = text_array[each_index:each_index+len(pattern_array)]
              
            for i in range(len(pattern_array)):
              text_array[each_index + i] = ''
            
            each_index += len(pattern_array)
            matched_flag = False
          
  temp = '\n'.join(text_array)
  temp = trim_newlines(temp)
  if number_of_matches > 0 and log:
    temp =  temp + '\n______________________________\n'+\
        'Replaced '+str(number_of_matches)+' instances of the following pattern: \n'+\
        '\n'.join(sample_replace)+'\n'+\
        '______________________________\n'
  return temp




# TODO: what if www resolves to multiple IPs? ex: google.com
# TODO: handle 'is an alias' case, ex: google.com
def dnslookup(ip_or_hostname):
  """
  <Purpose>
    Changes IPs to hostnames, and hostnames to IPs using the 'host' program on linux machines.

  <Arguments>
    ip_or_hostname:
      a string that is either the IP or a hostname
      
  <Exceptions>
    Raises an exception if host returns an unexpected value, or if there is 
    some error in the lookup.

  <Side Effects>
    None.

  <Returns>
    String.  Returns either the hostname or the IP or same string if a 
      reverse lookup can't be done.
  """

  # ip -> hostname and
  # hostname -> ip
  out, err, retcode = shellexec2('host '+ip_or_hostname)
  # sample strings:
  # 1. [ip] domain name pointer [hostname].
  # 2. [hostname] has address [ip]
  if retcode == 0:
    if out.find('domain name pointer') > -1:
      # this is of type 1, so return the hostname
      hostname = out.split(' ')[-1].strip('\r\n .')
      return hostname.lower()
    elif out.find('has address') > -1:
      # type 2, so return the IP
      ip = out.split(' ')[-1].strip('\r\n .')
      return ip
      # error
    else:
      raise Exception('Error in dnslookup: unexpected return value ('+str(out.strip('\n\r '))+')')
  else:
    if out.find('not found') > -1:
      # probably networkip
      return ip_or_hostname.lower()
    raise Exception('Error in dnslookup ('+str(retcode)+'): '+str(out)+', '+str(err)+' .')


def shellexec2(cmd_str):
  """
  <Purpose>
    Uses subprocess to execute the command string in the shell.
     
  <Arguments>
    cmd_str:  The string to be treated as a command (or set of commands,
                deploy_logging.separated by ;).
    
  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    A tuple containing (stdout, strerr, returncode)

    Detailed:
    stdout: stdout printed to console during command execution.
    strerr: error (note: some programs print to strerr instead of stdout)
    returncode: the return code of our call. If there are multiple commands, 
                then this is the return code of the last command executed.
  """

  # get a handle to the subprocess we're creating..
  handle = subprocess.Popen(cmd_str, shell=True, 
      stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

  # execute and grab the stdout and err
  stdoutdata, strerrdata = handle.communicate("")

  # The return code...  
  returncode = handle.returncode
  
  return stdoutdata, strerrdata, returncode
