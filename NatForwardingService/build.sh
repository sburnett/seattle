#!/bin/bash
#
# Builds the tests


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
cp ./tests/* ./built
cp ./app/* ./built



# copy files from a prepared test directory WITHOUT TESTS
# i.e don't use the -t option for preparetest
cd built/
my_files=`ls *.repy`

cp ../run_tests.py .
cp -s ../../${prepared_test_dir}/* .


# Pre-process each file
echo "#####"
echo "Building src files..."
echo "#####"


# Then process
for f in ${my_files}
do
  echo "Pre-processing: ${f}"
  python repypp.py ${f} ${f}.out # Process file
  rm ${f}  # Remove non-preprocessed
  mv ${f}.out ${f} # Replace it with the processed file
done

