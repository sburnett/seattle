#!/bin/sh

# When the program is installed on a user's
# comptuer, all instances of %PROG_PATH% will
# be replaced with the path to the program's
# directory

cd "%PROG_PATH%"

python get_seattlestopper_lock.py
python nmmain.py &
python softwareupdater.py &
echo "seattle has been started."