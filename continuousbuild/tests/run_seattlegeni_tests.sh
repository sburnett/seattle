#!/usr/bin/env bash

trunkdir=$1
logfile=$2
#find the first character. We need to check if it's a slash (indicating absolute path).
absolutemarker=${trunkdir:0:1}

if [ -z "$trunkdir" ] || [ -z "$logfile" ] || [ "$absolutemarker" != "/" ]; then
  echo "Usage: $0 trunkdir logfile (where trunkdir and logfile should be absolute paths, not relative ones)"
  exit 1
fi

$trunkdir/seattlegeni/tests/run_tests.sh $trunkdir >$logfile 2>&1

exit $?

