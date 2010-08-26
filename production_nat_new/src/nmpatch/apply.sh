#!/bin/bash

# compiling

cd ~/seattle/trunk/production_nat_new/src/ 
~/runtest.sh -c ShimStackInterface.repy
cp /tmp/seattle/out.ShimStackInterface.repy ~/seattle/nmpatch/ShimStackInterface.repy
echo 'ShimStackInterface compiled from trunk'

# applying patch

cd ~/seattle/nmpatch
cp ShimStackInterface.repy addme.py nmmain.py nmclient.repy sockettimeout.repy ../nm/seattle_repy/
echo 'Patch applied to nm'

# scp -q ShimStackInterface.repy addme.py nmmain.py nmclient.repy sockettimeout.repy hdanny@blackbox.cs.washington.edu:~/nm/seattle_repy/
# echo 'Patch applied to blackbox'

cp ShimStackInterface.repy nmclient.repy sockettimeout.repy ../demokit/
echo 'Patch applied to seash.'

scp -q ShimStackInterface.repy nmclient.repy sockettimeout.repy hdanny@blackbox.cs.washington.edu:~/deploy/seattle
echo 'Patch applied to seattlegeni'

