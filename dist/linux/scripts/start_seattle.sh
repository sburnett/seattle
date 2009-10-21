#!/bin/sh

# Change to the seattle directory (this "cd" command allows the user to call the
#   script from any directory.
cd "`echo $0 | sed 's/start_seattle.sh//'`"


python get_seattlestopper_lock.py
python nmmain.py &
python softwareupdater.py &


# Check to confirm that nmmain.py and softwareupdater.py are running, and print
#   the status to the user.
# For some rare systems, such as FreeBSD, the "-ef" options of "ps" cause an
#   error.  Thus, to see if the Node Manager and Software Updater are running on
#   such systems, there is a _SPECIAL call which does not use the "-ef" options
#   for the "ps" command.
# Further, any standard error output that may be generated from the "ps" command
#   is suppressed to /dev/null to avoid erroneous output to the user.
NMMAIN=`ps -ef 2>/dev/null | grep nmmain.py | grep -v grep`
NMMAIN_SPECIAL=`ps 2>/dev/null | grep nmmain.py | grep -v grep`
SOFTWAREUPDATER=`ps -ef 2>/dev/null | grep softwareupdater.py | grep -v grep`
SOFTWAREUPDATER_SPECIAL=`ps 2>/dev/null | grep softwareupdater.py | grep -v grep`

if echo "$NMMAIN" | grep nmmain.py > /dev/null
then
    if echo "$SOFTWAREUPDATER" | grep softwareupdater.py > /dev/null
    then
	echo "seattle has been started: $(date)"
    fi
elif echo "$NMMAIN_SPECIAL" | grep nmmain.py > /dev/null
then
    if echo "$SOFTWAREUPDATER_SPECIAL" | grep softwareupdater.py > /dev/null
    then
	echo "seattle has been started: $(date)"
    fi
else
    echo "seattle was not properly started."
    echo "If you continue to see this error, please contact the seattle" \
	"development team."
fi