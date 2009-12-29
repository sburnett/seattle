#!/bin/sh

cd "`echo $0 | sed 's/stop_seattle.sh//'`"

python stop_all_seattle_processes.py
echo "seattle has been stopped."