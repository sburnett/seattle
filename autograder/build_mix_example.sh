
# this is just an example of how to use this script, just change
# directory structure to work with your own.

IN=nm_remote_api.mix
OUT=nm_remote_api.py

# go to svn trunk location
cd ..

# dump repo into directory (auto_build directory MUST exist in trunk,
#                           just mkdir auto_build)
python preparetest.py auto_build

# copy .mix file to this directory
cp autograder/$IN auto_build/$IN

# go into the build directory
cd auto_build

# run it through the preprocessor
python repypp.py $IN $OUT


# place script into a seattle installation (seattle_repy/)
#cp $OUT ../../../autograder_stuff/attempt2_clean/repy_code/
cp $OUT ../autograder/emulab/