#!/bin/sh

# Change to the seattle directory (this "cd" command allows the user to call the
#   script from any directory.
cd "`echo $0 | sed 's/start_seattle.sh//'`"


python get_seattlestopper_lock.py
python nmmain.py &
python softwareupdater.py &


# Check to confirm that nmmain.py and softwareupdater.py are running, and print
#   the status to the user.
# Some systems respond different to some options passed to 'ps', so we use
#   'ps auxww' to create a universal command that will tell us if nmmain.py
#   is currently running.
#
#   'ps axww':
#     'ax': shows all processes
#     'ww': makes sure that the output is not limited by column length.
#     

NMMAIN=`ps axww 2>/dev/null | grep nmmain.py | grep -v grep`
SOFTWAREUPDATER=`ps axww 2>/dev/null | grep softwareupdater.py | grep -v grep`


if echo "$NMMAIN" | grep nmmain.py > /dev/null
then
    if echo "$SOFTWAREUPDATER" | grep softwareupdater.py > /dev/null
    then
	echo "seattle has been started: $(date)"
    fi
else
    echo "seattle was not properly started."
    echo "If you continue to see this error, please contact the seattle" \
	"development team."
fi