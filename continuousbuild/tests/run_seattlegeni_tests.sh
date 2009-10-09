#!/bin/bash

trunkdir=$1
logfile=$2

if [ -z "$trunkdir" ] || [ -z "$logfile" ]; then
  echo "Usage: $0 trunkdir logfile (where logfile should be an absolute path, not a relative one)"
  exit 1
fi

$trunkdir/seattlegeni/tests/run_tests.sh $trunkdir >$logfile 2>&1

exit $?

