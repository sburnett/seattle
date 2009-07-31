#!/bin/sh

cd `echo $0 | sed 's/stop_seattle.sh//'`

python impose_seattlestopper_lock.py&
echo "seattle has been stopped."