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
import send_gmail

svn_repo_path = '/var/local/svn/'
notify_list = ["ivan@cs.washington.edu", "justinc@cs.washington.edu", 'jaehong@u.washington.edu']

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
  sprints = []
  sprint_template = {'date' : '', 'force' : '', 'users' : []}
  format = ['date', 'force', 'users']
  sprint = None

  for line in milestones_txt.split('\n'):
      if line is '' or line.startswith('#'):
          continue
      
      if line.startswith(':sprint'):
          if sprint != None:
              sprints.append(sprint)
          sprint = deepcopy(sprint_template)
          field_index = 0
          field = format[field_index]
          continue

      if field == 'users':
          line
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

  # setup gmail lib
  gmail_user, gmail_pwd = open("/var/local/svn/hooks/gmail_account","r").read().strip().split()
  send_gmail.init_gmail(gmail_user=gmail_user, gmail_pwd=gmail_pwd)

  # check if any of the sprint personnel are past deadline
  for sprint in parse_sprints(milestones_txt):
      sprint_date = datetime.strptime("%s 23:59:59"%(sprint['date']), "%m/%d/%Y %H:%M:%S")
      if sprint_date < datetime.now():
          # sprint in the past
          notify = False
          notify_str = ""
          # check if we need to notify
          for user in sprint['users']:
              if not user.startswith['X']:
                  notify_str += '''
User            %s
Deadline        %s
Strike force    %s'''%(user,sprint['date'],sprint['force']) + '\n'
                  notify = True
          
          if notify:
              # send email to notify_list members
              for email in notify_list:
                  send_gmail.send_gmail(email, "user(s) failed to meet sprint deadline %s"%(sprint['date']))
              
if __name__ == "__main__":
  sys.exit(main())
