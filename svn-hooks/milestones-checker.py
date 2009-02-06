#!/usr/bin/python
"""
<Program Name>
  milestones-checker.py

<Started>
  January 12, 2008

<Author>
  ivan@cs.washington.edu
  Ivan Beschastnikh

<Purpose>
  Used as a cronscript that will check if any of the strike
  forces personnel are late on their milestones sprints

<Usage>
  python milestones-checker
  
"""

import os
import sys
import subprocess
from copy import deepcopy
from datetime import datetime

enable_email = True
svn_repo_path = '/var/local/svn/'
notify_list = ['seattle-devel@cs.washington.edu']
#notify_list = ['bestchai@gmail.com']



if enable_email:
  import send_gmail


  
def command_output(cmd):
  """
  <Purpose>
      Runs command 'cmd' and returns its stdout output after it completes.

  <Arguments>
      cmd:
         command line to execute in a separate process

  <Exceptions>
      None

  <Side Effects>
      Unknown -- depends on cmd argument

  <Returns>
      Output from running cmd.
  """
  return subprocess.Popen(cmd.split(), stdout=subprocess.PIPE).communicate()[0]





def parse_sprints(sprints_txt):
  """
  <Purpose>


  <Arguments>


  <Exceptions>


  <Side Effects>


  <Returns>

  """
  sprints = []
  sprint_template = {'date' : '', 'force' : '', 'users' : []}
  format = ['date', 'force', 'users']
  sprint = None
  field = None
  for line in sprints_txt.split('\n'):
      if line is '' or '#' in line:
          continue
      
      if line.startswith(':sprint'):
          if sprint != None:
              sprints.append(sprint)
          sprint = deepcopy(sprint_template)
          field_index = 0
          field = format[field_index]
          continue
      
      if field == None:
        # syntax error
        return None
      if field == 'users':
          sprint[field].append(line)
      else:
          sprint[field] = line
          field_index += 1
          field = format[field_index]

  if sprint != None:
      sprints.append(sprint)

  return sprints




def main():
  """
  <Purpose>
      Checks out milestones.txt from the repository. Interprets
      it and sends email if anyone is late on their sprints.
  
  <Arguments>
      None
  
  <Exceptions>
      Not sure.

  <Side Effects>
      Sends email.

  <Returns>
      Returns 1 if anyone is late. Otherwise returns 0.
  """
  global notify_list
  global svn_repo_path

  # grab latest milestones revision from the repo
  milestones_txt = command_output("svn cat http://seattle.cs.washington.edu/svn/seattle/trunk/milestones.txt")
  
# failure example:
#  milestones_txt = """
#:sprint
#01/01/2009
#eye candy
#789 alper parallelize resource acquisition and release
#sean redesign GENI portal
#"""

  # setup gmail lib
  if enable_email:
    gmail_user, gmail_pwd = open("/var/local/svn/hooks/gmail_account","r").read().strip().split()
    send_gmail.init_gmail(gmail_user=gmail_user, gmail_pwd=gmail_pwd)

  # check if any of the sprint personnel are past deadline
  sprints = parse_sprints(milestones_txt)
  if sprints is None:
    # syntax error in parsing milestones_txt
    print "syntax error in parsing milestones file"
    if enable_email:
      # send email to notify_list members
      for email in notify_list:
        send_gmail.send_gmail(email, "svn-hook milestokes-checker syntax error in milestones file", "", "")
    return 1
    
  for sprint in sprints:
      sprint_date = datetime.strptime("%s 00:00:00"%(sprint['date']), "%m/%d/%Y %H:%M:%S")
      # print sprint_date
      if sprint_date <= datetime.now():
          if sprint['date'] == datetime.now().strftime("%m/%d/%Y"):
            # sprint due today
            notify = True
          else:
            # sprint in the past
            notify = False
            
          notify_str = '''
For the %s sprint for the %s strike force:

'''%(sprint['date'], sprint['force'])
          # check if we need to notify
          for user in sprint['users']:
            try:
              rev = "Completed as of revision %i"%(int(user.split(' ')[0]))
              task = ' '.join(user.split(' ')[2:])
              user = user.split(' ')[1]
            except ValueError:
              rev = "Failed to complete"
              # always notify when someone failed in a sprint
              notify = True
              task = ' '.join(user.split(' ')[1:])
              user = user.split(' ')[0]
              
            notify_str += '''
User            %s
Task            %s
%s'''%(user, task, rev) + '\n\n'
          
          if notify:
            print notify_str
            if enable_email:
              # send email to notify_list members
              for email in notify_list:
                send_gmail.send_gmail(email, "[status] strike force: %s, sprint: %s"%(sprint['force'], sprint['date']), notify_str, "")
  return 0






if __name__ == "__main__":
  sys.exit(main())
