#!/bin/bash

# This script is used to check whether the nodemanager and softwareupdater
# are running on a node. The script takes an IP address and login username.

IP=$1
USERNAME=$2

# Check to see if we were able to ssh into a node.
function check_connection {
  local output=$1
  test=`echo $output | grep "No route to host"`
  test2=`echo $output | grep "Connection timed out"`
  test3=`echo $output | rgrep "Permission denied"`
  test4=`echo $output | rgrep "Connection refused"`
  test5=`echo $output | rgrep "Name or service not known"`
  test6=`echo $output | rgrep "vserver ... suexec"`

  if [ -n "$test" ] || [ -n "$test2" ] || [ -n "$test3" ] || [ -n "$test4" ] || [ -n "$test5" ] || [ -n "$test6" ]; then
    echo "$IP is down. $test $test2 $test3 $test4 $test5 $test6 $test7"
    exit
  fi
}

# SSH into a node.
output=`ssh -l $USERNAME -o ConnectTimeout=10 -o UserKnownHostsFile=/dev/null -o PasswordAuthentication=no -o StrictHostKeyChecking=no $IP "ps -ef" 2>&1`
check_connection "$output"


# Check to see if nodemanager and software updater are running.
nodemanager_running=`echo $output | rgrep "nmmain"`
softwareupdater_running=`echo $output | rgrep "softwareupdater"`

if [ -n "$nodemanager_running" ] && [ -n "$softwareupdater_running" ]; then
    echo "Nodemanager and softwareupdater running on $IP"
elif [ -n "$nodemanager_running" ] && [ -z "$softwareupdater_running" ]; then
    echo "Only nodemanager is running on $IP"
elif [ -z "$nodemanager_running" ] && [ -n "$softwareupdater_running" ]; then
    echo "Only softwareupdater is running on $IP"
else
    echo "Neither nodemanager or softwareupdater are running on $IP"
fi

