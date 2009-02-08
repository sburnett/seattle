#!/bin/bash
#
# Starts the forwarder on localhost, port 12345

# Where to store the PID
pidfile="./run/forwarder.pid"

if [ -f ${pidfile} ]
then
  kill `cat ${pidfile}`
  rm ${pidfile}
fi