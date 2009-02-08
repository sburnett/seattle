#!/bin/bash
#
# Starts the forwarder on localhost, port 12345

# Where to store the PID
pidfile="./run/forwarder.pid"
outlog="./log/forwarder.out"
errlog="./log/forwarder.err"

# What to call
python repy.py restrictions.forwarder forwarder.py "127.0.0.1" 12345 2>${errlog} >${outlog} &

# Save the PID to a file
PID=$!
echo $PID > "$pidfile"