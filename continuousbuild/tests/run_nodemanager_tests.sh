#!/usr/bin/env bash

trunkdir=$1
logfile=$2

if [ -z "$trunkdir" ] || [ -z "$logfile" ]; then
  echo "Usage: $0 trunkdir logfile (where logfile should be an absolute path, not a relative one)"
  exit 1
fi

# A mktemp command that works on mac/bsd and linux.
tmpdir=`mktemp -d -t tmp.XXXXXXXX` || exit 1

# Change directory to the directory that preparetest.py is in.
cd $trunkdir

python preparetest.py -tr $tmpdir > /dev/null
cd $tmpdir

python utf.py -T -m nm >$logfile 2>&1

result=$?

rm -rf $tmpdir

if [ "$result" != "0" ]; then
  echo "utf nm tests didn't run properly"
  exit 1
fi

#The words that indicate something went wrong in utf are "FAIL" and "ERROR".
FAILURE_WORDS="FAIL ERROR"

for word in `echo $FAILURE_WORDS`; do
  if [ ! -z "`grep -F \"$word\" $logfile`" ]; then
    echo "Encountered failure word '$word' in logfile."
    exit 1
  fi
done

#TODO(sjs25): Add a Count functionality to UTF
#(commented code left here intentionally)
#SUCCESS_STRING=" tests passed, 0 tests failed"

#if [ -z "`grep -F \"$SUCCESS_STRING\" $logfile`" ]; then
 # echo "Did not find success string '$SUCCESS_STRING' in logfile."
 # exit 1
#fi
