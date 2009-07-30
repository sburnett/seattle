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

# Copy resource files
echo "Copying Resource files..."
cp ./resource/* ./built/

# Copy the scripts directory
echo "Copying Script files..."
cp -R ./scripts ./built/

# copy files from a prepared test directory WITHOUT TESTS
# i.e don't use the -t option for preparetest
cd built/
cp -s ../../${prepared_test_dir}/* .


# Copy multiplexer files
# Go into the source
cd ../../multiplexer/src

echo "#####"
echo "Copying Multiplexer files..."
echo "#####"
all_mux_files=`ls *.py`
for f in ${all_mux_files}
do
  echo "Copying: ${f}"
  cp ${f} ../../natlayer/built/${f} # Copy original file
done

cd ../../natlayer/built/

# Then process
for f in ${all_mux_files}
do
  echo "Pre-processing: ${f}"
  python repypp.py ${f} ${f}.out # Process file
  rm ${f}  # Remove non-preprocessed
  mv ${f}.out ${f} # Replace it with the processed file
done

# Go into the source
cd ../src

# Pre-process each file
echo "#####"
echo "Building src files..."
echo "#####"
all_files=`ls *.py`

# Copy each file
for f in ${all_files}
do
  echo "Copying: ${f}"
  cp ${f} ../built/${f} # Copy original file
done

# Go into built
cd ../built

# Then process
for f in ${all_files}
do
  echo "Pre-processing: ${f}"
  python repypp.py ${f} ${f}.out # Process file
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
  python repypp.py ${f}_pre ${f}
  rm ${f}_pre # Remove the original
  cd ../tests
done

echo "#####"
echo "Done"
