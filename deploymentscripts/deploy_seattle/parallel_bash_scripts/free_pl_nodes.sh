#!/bin/bash

# This script is used to check if this node already has a seattle* directory under the 
# home directory on the node. A lazy way of checking if Seattle has been installed on
# this machine. If there are no Seattle installation on this node then the IP address
# gets added to the file: free_planetlab_nodes.txt

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

output=`ssh -l $USERNAME -o ConnectTimeout=15 -o UserKnownHostsFile=/dev/null -o PasswordAuthentication=no -o StrictHostKeyChecking=no $IP "ls" 2>&1`

check_connection "$output"

seattle_installed=`echo $output | rgrep "seattle"`

CURDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

if [ -z "$seattle_installed" ]; then
    echo "Seattle available on $IP"
    echo "$IP" >> $CURDIR/../free_planetlab_nodes.txt
fi