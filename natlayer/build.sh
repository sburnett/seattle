#!/bin/bash
#
# Builds the tests

# Remove everything in the build dir
echo "Removing old built files..."
rm -Rf ./built/*

# Copy resource files
echo "Copying Resource files..."
cp ./resource/* ./built/

# Copy the scripts
echo "Copying Script files..."
cp -R ./scripts ./built/

# Make some directories
mkdir ./built/log
mkdir ./built/run

# Go into the source
cd src

# Pre-process each file
echo "Building src files..."
echo "#####"
all_files=`ls *.py`
for f in ${all_files}
do
  echo "Pre-processing: ${f}"
  cp ${f} ../built/${f}_pre # Copy original file
  cd ../built
  python ../../seattlelib/repypp.py ${f}_pre ${f} # Process file
  rm ${f}_pre # Remove the original
  cd ../src
done

# Go into the source
cd ../tests

# Pre-process each test file
echo "#####"
echo "Building test files..."
echo "#####"
all_files=`ls *.py`
for f in ${all_files}
do
  echo "Pre-processing: ${f}"
  cp ${f} ../built/${f}_pre # Copy original file
  cd ../built
  python ../../seattlelib/repypp.py ${f}_pre ${f} # Process file
  rm ${f}_pre # Remove the original
  cd ../tests
done

echo "#####"
echo "Done"