#!/bin/bash
#
# Runs the tests
# Takes 1 optional parameter: class
# If class parameter is given, then only test_CLASS_*.py will be run

# If we get a SIGINT, do we terminate the test(1) or exit(0)
SIGINTACT="1"

# Should we block stderr? This prevents ugly error messages when SIGINT is received
BLOCKERR="1"

#function stop_forwarder() {
#	# stop the forwarder
#	echo "Stopping forwarder!"
#	./scripts/stop_forwarder.sh >/dev/null 2>&1
#}

# If the script is interrupted (Control-C) handle this cleanly
function interrupt() {
	# Terminate the current test
	printf "[ SIGINT ]\n"
	if [ $SIGINTACT -eq "1" ]
	then
		kill $CURPID 2>&1 >/dev/null
	else
		echo "#####"
		echo "Caught User Interrupt!"
		#stop_forwarder
		exit	
	fi
}

# Give the user a heads up as ot the expected behavior
if [ $SIGINTACT -eq "1" ]
then
  echo "INFO: SIGINT ( Control-C ) will terminate the currently executing test"
else
  echo "INFO: SIGINT ( Control-C ) will stop the execution of run_tests.sh"
fi

# We don't want output from sub-shells
if [ $BLOCKERR -eq "1" ]
then
  exec 2>/dev/null
fi

# The PID of the current test
CURPID=0

# Go into the built dir
cd built

# Clean old logs
LOGCOUNT=`ls log/ | grep -c ""`
if [ ${LOGCOUNT} -gt "0" ]
then
  echo "Archiving old logs..."
  DATE=`date +%s`
  NAME=logs.${DATE}.tar
  tar -cf ${NAME} log/*
  echo "Created Archive: ${NAME}"
  echo "Clearing old logs..."
  rm -f ./log/*
fi

# Stop the old forwarder if it is running
#if [ -f run/forwarder.pid ]
#then
#  echo "Stopping old forwarder..."
#  ./scripts/stop_forwarder.sh
#fi

#echo "Starting forwarder..."
#./scripts/start_forwarder.sh

# Setup interrupt handler
trap "interrupt" SIGINT

# Sleep for a second, give the forwarder a change to start
#echo "Waiting for forwarder to initialize..."
#sleep 5

#forwarderpid=`cat ./run/forwarder.pid`

# Check if the forwarder is still running
#forwarderstat=`ps -p ${forwarderpid} | grep -c ""`
#if [ ${forwarderstat} -eq "1" ]
#then
#      echo "Fatal Error! Forwarder has not started!"
#      rm ./run/forwarder.pid
#      exit
#fi

# Pre-process each file
echo "Running tests..."
echo "#####"

# Run only selected test "class" if there is a parameter
if [ $# -gt "0" ]
then
  all_tests=`ls test_$1_*.py`
else
  all_tests=`ls test_*.py`
fi

for f in ${all_tests}
do
  printf "Running %-60s" ${f}
  
  # Log the output
  run="python repy.py --logfile log/${f}.log restrictions.default ${f}"
  ${run} & >/dev/null 2>&1
  
  # Save the current PID
  CURPID=$!

  # Wait for that to finish 
  wait >/dev/null 2>&1

  # Get exit code
  EXITCODE=$?
  
  # Only print if the process has a clean exit code
  # This is so SIGINT will print [ SIGINT ]
  if [ $EXITCODE = 0 ]
  then
    # Check if the log size is 0
    size=`cat ./log/${f}.log.old | grep -c ''`
    if [ ${size} -eq "0" ]
    then
      printf "  [ PASSED ]\n"
    else
      printf "  [ FAILED ]\n"
    fi
  fi

  # Sleep for a second
  sleep 2
  
  # Check if the forwarder is still running
  #forwarderstat=`ps -p ${forwarderpid} | grep -c ""`
  #if [ ${forwarderstat} -eq "1" ]
  #then
  #    echo "Fatal Error! Forwarder Dead!"
  #    rm ./run/forwarder.pid
  #    exit
  #fi
done

echo "#####"
echo "Done!"

# Stop the forwarder
#stop_forwarder
