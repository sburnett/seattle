
# this is just an example of how to use this script, just change
# directory structure to work with your own.

IN=nm_remote_api.mix
OUT=nm_remote_api.py
TESTDIR=buildtest

### these lines should be commented out if a test directory is allready prepared
#cd ../../
#mkdir ${TESTDIR}
#python preparetest.py -t ${TESTDIR}/
#cd autograder/emulab
###end commented out section



# Make the built directory if necessary
mkdir ./built/

# Remove everything in the build dir
echo "Removing old built files..."
rm -Rf ./built/*


#copy the files we need to the built directory
cp ../${IN} built/
cp autograder_runner.py built/
cp data_interface.py built/
cp remote_emulab.py built/
cp sshxmlrpc.py built/
cp ../nm_remote_api.mix built/
cp repypp.py built/
cp parallelize.repy built/

cd built

# link in needed repy files
cp -r  ../../../repy/* .
#ln -s ../../../${TESTDIR}/repy.py repy.py
#ln -s ../../../${TESTDIR}/repypp.py repypp.py
#ln -s ../../../${TESTDIR}/repyhelper.py repyhelper.py
cp -r ../../../${TESTDIR}/* .

#make directories for test runs
mkdir to_grade
mkdir graded
mkdir status
mkdir meta_test

# get some stuff to grade
cp ../lan.ns meta_test/
cp -r ../../../assignments/webserver/webserver_tests/* meta_test/
cp ../../../assignments/webserver/webserver.repy to_grade

cd to_grade
tar -cf joe.tar webserver.repy
rm webserver.repy

cd ../status
touch joe.tar.txt

cd ..

# run aplers thing though the preprocessor
python repypp.py $IN $OUT

