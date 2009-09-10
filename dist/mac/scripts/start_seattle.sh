#!/bin/sh

# When the program is installed on a user's
# comptuer, all instances of %PROG_PATH% will
# be replaced with the path to the program's
# directory

cd "`echo $0 | sed 's/start_seattle.sh//'`"

python get_seattlestopper_lock.py
python nmmain.py &
python softwareupdater.py &
echo "seattle has been started: $(date)"