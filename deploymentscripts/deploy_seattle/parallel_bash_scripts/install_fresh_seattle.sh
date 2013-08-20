#!/bin/bash

# This script is used install a fresh instance of Seattle on this node.
# The script first uninstalls and removes any old instance of seattle running
# directly in the home directory. Then it downloads a new Seattle installer,
# untars the tar file and runs the installer.

# This script takes the IP address of the node, the username to use to login
# and the seattle username from which to download the installer.

IP=$1
USERNAME=$2
SEATTLEUSER=$3

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


# Uninstalls/removes old seattle then downloads and installs a fresh instance of Seattle.
output=`ssh -l $USERNAME -o ConnectTimeout=15 -o UserKnownHostsFile=/dev/null -o PasswordAuthentication=no -o StrictHostKeyChecking=no $IP "rm -rf /home/$USERNAME/*; wget --no-check-certificate https://seattleclearinghouse.poly.edu/download/$SEATTLEUSER/seattle_linux.tgz; tar -zxvf /home/$USERNAME/seattle_linux.tar.gz; tar -zxvf /home/$USERNAME/seattle_linux.tgz; /home/$USERNAME/seattle/uninstall.sh; rm yes.txt; echo "yes" > /home/$USERNAME/yes.txt; /bin/bash /home/$USERNAME/seattle/install.sh > /dev/null 2> /dev/null < /home/$USERNAME/yes.txt; sleep 10; rm /home/$USERNAME/yes.txt;"`
check_connection $output





