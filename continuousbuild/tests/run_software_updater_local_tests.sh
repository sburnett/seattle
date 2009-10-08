#!/bin/bash

trunkdir=$1
logfile=$2

if [ -z "$trunkdir" ] || [ -z "$logfile" ]; then
  echo "Usage: $0 trunkdir logfile (where logfile should be an absolute path, not a relative one)"
  exit 1
fi

tmpdir=`mktemp -d`

# softwareupdater/run_local_tests.sh must be run from the same directory that
# preparetests.py is in.

cd $trunkdir

softwareupdater/run_local_tests.sh $tmpdir >$logfile 2>&1

if [ "$?" != "0" ]; then
  echo "run_local_tests.sh didn't run properly"
  rm -rf $tmpdir
  exit 1
fi

rm -rf $tmpdir

FAILURE_WORDS="fail exception traceback"

for word in `echo $FAILURE_WORDS`; do
  if [ ! -z "`grep -i $word $logfile`" ]; then
    echo "Encountered failure word '$word' in logfile."
    exit 1
  fi
done

