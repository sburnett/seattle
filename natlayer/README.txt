Directory Structure is as follows:

build.sh       - This prepares everything to run, and places everything in built
built/         - This contains all the pre-processed files and everything necessary to run the unit tests
built/log/     - Contains any logs from the forwarder, server, client, or tests.
built/run/     - Contains .pid files for applications that are running (e.g. the forwarder)
built/scripts/ - Contains some helper shell scripts that are copied from scripts
resource/      - This contains library files that are included but not processed (e.g. restriction files)
run_tests.sh   - This file will run the unit tests
scripts/       - Contains helper shell scripts
src/           - Contains any python src files
tests/         - Contains the unit tests
 * Tests should be named test_TESTNAME.py or if a specified order is preferred, you can name test_0_TESTNAME.py or test_1_TESTNAME.py
 * since the tests will be reported alphabetically, you can use 0-9 as priority levels.