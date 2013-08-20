#!/bin/bash

# This script is used to check the amount of memory and cpu that
# is being used by the nodemanager and the softwaremanager.
# The script takes the IP address and the username to login with.

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
    echo "$IP is down."
    exit
  fi
}

output_nm=`ssh -l $USERNAME  -o ConnectTimeout=15 -o UserKnownHostsFile=/dev/null -o PasswordAuthentication=no -o StrictHostKeyChecking=no -q $IP "ps ax -o %cpu,%mem,cmd | grep nmmain | grep -v grep" 2>&1`

check_connection "$output_nm"

output_software=`ssh -l $USERNAME  -o ConnectTimeout=15 -o UserKnownHostsFile=/dev/null -o PasswordAuthentication=no -o StrictHostKeyChecking=no -q $IP "ps ax -o %cpu,%mem,cmd | grep softwareupdater | grep -v grep" 2>&1`

check_connection "$output_software"


echo "$IP ---------------- $output_nm, $output_software"

