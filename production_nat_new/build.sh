#!/bin/bash
#
# Builds the tests

# PRE CONDITION 
# from trunk run python preparetest ${prepared_test_dir}

prepared_test_dir='basictest'


# Make the built directory if necessary
mkdir ./built/

# Remove everything in the build dir
echo "Removing old built files..."
rm -Rf ./built/*

# Recreate the folders we need
mkdir ./built/log/
mkdir ./built/run/
mkdir ./built/output

# Copy resource files
echo "Copying Resource files..."

cp ./src/* ./built
cp ./test/* ./built


cd built/
test_files=`ls *.py`
src_files=`ls *.repy`

cp -s ../../${prepared_test_dir}/* .


# Pre-process each file
echo "#####"
echo "Building src files..."
echo "#####"


# Then process
for f in ${src_files}
do
  echo "Pre-processing src file: ${f}"
  python repypp.py ${f} ${f}.out # Process file
  rm ${f}  # Remove non-preprocessed
  mv ${f}.out ${f} # Replace it with the processed file
done

for f in ${test_files}
do
  echo "Pre-processing test file: ${f}"
  python repypp.py ${f} ${f}.out # Process file
  rm ${f}  # Remove non-preprocessed
  mv ${f}.out ${f} # Replace it with the processed file
done

