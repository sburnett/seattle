#!/bin/bash

# Usage:
#       Assuming that you are in the same directory as remote_server.py, do:
#	run_remote_server.sh
#
# Description:
#	run remote_server.py on seattle.cs.washington.edu

python ./remote_server.py seattle.cs.washington.edu 9090 /var/www/installers/
