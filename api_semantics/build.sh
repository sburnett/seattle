#!/bin/bash
#

# Make the built directory if necessary
mkdir ./built/

# Remove everything in the build dir
echo "Removing old built files..."
rm -Rf ./built/*



# copy each test directory
cp -r ./tests/* ./built


cd built
all_tests=`ls`
for f in ${all_tests}
do
    cp ../resource/* ${f}/
    ln -s ../../../repy/repy.py ${f}/repy.py
done




echo "Done"
