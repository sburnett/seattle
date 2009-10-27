#!/bin/bash

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

python preparetest.py -t $tmpdir
cd $tmpdir

python nminit.py >$logfile.nminit 2>&1 &
python nmmain.py >$logfile.nmmain 2>&1 &

# Give them time to start.
sleep 60

python run_tests.py -n >$logfile 2>&1

result=$?

rm -rf $tmpdir

echo "------------ nminit.log --------------" >> $logfile
cat $logfile.nminit >> $logfile
rm $logfile.nminit
echo "------------ nmmain.log --------------" >> $logfile
cat $logfile.nmmain >> $logfile
rm $logfile.nmmain

if [ "$result" != "0" ]; then
  echo "run_tests.sh didn't run properly"
  exit 1
fi

# We don't include "exception" because it is in the name of some of the tests
# themselves which end up in the log file.
FAILURE_WORDS="[failed] failure: traceback"

for word in `echo $FAILURE_WORDS`; do
  if [ ! -z "`grep -iF \"$word\" $logfile`" ]; then
    echo "Encountered failure word '$word' in logfile."
    exit 1
  fi
done

SUCCESS_STRING=" tests passed, 0 tests failed"

if [ -z "`grep -F \"$SUCCESS_STRING\" $logfile`" ]; then
  echo "Did not find success string '$SUCCESS_STRING' in logfile."
  exit 1
fi

