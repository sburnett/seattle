#!/bin/bash

# This script is used to do a lazy check on weather Seattle has already been 
# installed on this node. The script logs into the machine and checks for
# any directory or files starting with seattle*
# This script takes the IP address of the machine along with the username to
# login with.

IP=$1
USERNAME=$2

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

output=`ssh -l $USERNAME -o ConnectTimeout=15 -o UserKnownHostsFile=/dev/null -o PasswordAuthentication=no -o StrictHostKeyChecking=no $IP "ls" 2>&1`

check_connection "$output"

seattle_installed=`echo $output | rgrep "seattle"`
#echo "$IP....$output"

if [ -n "$seattle_installed" ]; then
    echo "Seattle already installed on $IP"
    #echo "$IP" >> free_planetlab_nodes.txt
fi
