#!/usr/bin/env bash

trunkdir=$1
logfile=$2

if [ -z "$trunkdir" ] || [ -z "$logfile" ]; then
  echo "Usage: $0 trunkdir logfile (where logfile should be an absolute path, not a relative one)"
  exit 1
fi

# A mktemp command that works on mac/bsd and linux.
tmpdir=`mktemp -d -t tmp.XXXXXXXX` || exit 1

# softwareupdater/test/run_local_tests.sh must be run from the same directory that
# preparetests.py is in.

cd $trunkdir

softwareupdater/test/run_local_tests.sh $tmpdir >$logfile 2>&1

if [ "$?" != "0" ]; then
  echo "run_local_tests.sh didn't run properly"
  rm -rf $tmpdir
  exit 1
fi

rm -rf $tmpdir

#We fail if UTF log contains FAIL or ERROR.
FAILURE_WORDS="FAIL ERROR"

for word in `echo $FAILURE_WORDS`; do
  if [ ! -z "`grep -i $word $logfile`" ]; then
    echo "Encountered failure word '$word' in logfile."
    exit 1
  fi
done

