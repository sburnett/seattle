#!/bin/bash

# This script is used to start up seattle on a node. It runs the start_seattle.sh
# script on the node.
# The script takes an IP address and a username.

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

output=`ssh -l $USERNAME -q -o ConnectTimeout=15 -o UserKnownHostsFile=/dev/null -o PasswordAuthentication=no -o StrictHostKeyChecking=no $IP "/bin/bash /home/$USERNAME/seattle/start_seattle.sh; exit" 2>&1`

check_connection $output

seattle_started=`echo $output | rgrep "seattle has been started"`
seattle_needs_install=`echo $output | rgrep "seattle must first be installed before the start_seattle.sh"`
#  seattle_installed=`echo $output | rgrep "seattle was already installed"`

if [ -n "$seattle_started" ]; then
    echo "Seattle started on $IP"
elif [ -n "$seattle_needs_install" ]; then
    echo "Seattle needs to be installed on $IP"
    echo $IP >> pl_nodes_need_install.txt
else
    echo "Failed to start Seattle on $IP. $output"
fi
