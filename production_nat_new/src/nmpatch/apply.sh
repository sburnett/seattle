#!/bin/bash

# compiling

# cd ~/seattle/trunk/production_nat_new/src/
# ~/runtest.sh -c ShimStackInterface.repy
# echo 'ShimStackInterface compiled from trunk'


# # applying patch

# cd ~/seattle/trunk/production_nat_new/src/nmpatch
# cp /tmp/seattle/out.ShimStackInterface.repy ShimStackInterface.repy
# python removeComments.py

#cp ShimStackInterface.repy addme.py nmmain.py nmclient.repy sockettimeout.repy ~/seattle/nm/seattle_repy/
#echo 'Patch applied to nm'

cp ShimStackInterface.repy nmmain.py sockettimeout.repy nmclient.repy /tmp/test/
echo 'Patch applied to test directory.'

# cp ShimStackInterface.repy addme.py nmmain.py nmclient.repy sockettimeout.repy ~/seattle/nm-win/seattle_repy/
# echo 'Patch applied to nm-win'

#cp ShimStackInterface.repy nmclient.repy sockettimeout.repy ~/seattle/demokit/
#echo 'Patch applied to seash.'

# scp -q ShimStackInterface.repy nmclient.repy sockettimeout.repy hdanny@blackbox.cs.washington.edu:~/deploy/seattle
# ssh hdanny@blackbox.cs.washington.edu 'rm ~/deploy/seattle/*_repy.py'
# echo 'Patch applied to seattlegeni'

# cd ~/seattle
# rm emma.tgz
# tar cfz emma.tgz nm
# rm emma-win.tgz
# tar cfz emma-win.tgz nm-win
# echo 'Created emma tarball'
