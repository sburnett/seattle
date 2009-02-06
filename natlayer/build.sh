#!/bin/bash
#
# Builds the tests

# Make the built directory if necessary
mkdir ./built/

# Remove everything in the build dir
echo "Removing old built files..."
rm -Rf ./built/*

# Recreate the folders we need
mkdir ./built/log/
mkdir ./built/run/

# Copy resource files
echo "Copying Resource files..."
cp ./resource/* ./built/

# Copy the scripts directory
echo "Copying Script files..."
cp -R ./scripts ./built/

# Go into the source
cd src

# Pre-process each file
echo "Building src files..."
echo "#####"
all_files=`ls *.py`

# Copy each file
for f in ${all_files}
do
  echo "Copying: ${f}"
  cp ${f} ../built/${f} # Copy original file
done

# Then process
cd ../built
for f in ${all_files}
do
  echo "Pre-processing: ${f}"
  python ../../seattlelib/repypp.py ${f} ${f}.out # Process file
  rm ${f}  # Remove non-preprocessed
  mv ${f}.out ${f} # Replace it with the processed file
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
  # Pre-process the file
  python ../../seattlelib/repypp.py ${f}_pre ${f}
  rm ${f}_pre # Remove the original
  cd ../tests
done

echo "#####"
echo "Done"
