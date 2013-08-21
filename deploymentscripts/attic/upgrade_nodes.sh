#!/bin/sh

echo '1...',
./uninstall.sh
rm -rf v*
cd ..


echo '2'
rm -rf deploy.temp
mkdir deploy.temp
cd deploy.temp

echo '3'
`cd deploy.temp; wget https://seattlegeni.cs.washington.edu/geni/download/flibble/seattle_linux.tgz ; tar -xf seattle_linux.tgz`

echo '4'
cd ..
cp -rf deploy.temp/seattle_repy/ ./

echo  '5'
cd seattle_repy

./install.sh > /dev/null 2> /dev/null < /dev/null&
echo '6'
