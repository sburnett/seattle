
# this is just an example of how to use this script, just change
# directory structure to work with your own.

IN=install_autograder.mix
OUT=install_autograder.py

# go to svn trunk location
cd ../../svn_seattle/trunk

# dump repo into directory (auto_build directory MUST exist in trunk,
#                           just mkdir auto_build)
python preparetest.py auto_build

# copy .mix file to this directory
cp ../../autograder_stuff/attempt2_clean/$IN auto_build

# go into the build directory
cd auto_build

# run it through the preprocessor
python repypp.py $IN $OUT

# place script into a seattle installation (seattle_repy/)
cp $OUT ../../../autograder_stuff/attempt2_clean/repy_code/