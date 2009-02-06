#!/bin/bash
#
# Runs the tests

# Go into the built dir
cd built

# Start the forwarder
cd scripts
echo "Starting forwarder..."
./start_forwarder.sh
cd ..

# Sleep for a second, give the forwarder a change to start
echo "Waiting for forwarder to initialize..."
sleep 5

forwarderpid=`cat ./run/forwarder.pid`

# Pre-process each file
echo "Running tests..."
echo "#####"
all_tests=`ls test_*.py`
for f in ${all_tests}
do
  printf "Running ${f}\t\t"
  
  # Log the output
  python ../../repy/repy.py --logfile log/${f}.log restrictions.default ${f}

  # Check if the log size is 0
  size=`cat ./log/${f}.log.old | grep -c ''`
  if [ ${size} -eq "0" ]
  then
    printf "PASSED!\n"
  else
    printf "FAILED!\n"
  fi
  
  # Sleep for a second
  sleep 1
  
  # Check if the forwarder is still running
  forwarderstat=`ps -p ${forwarderpid} | grep -c ""`
  if [ ${forwarderstat} -eq "1" ]
  then
      echo "Fatal Error! Forwarder Dead!"
      exit
  fi
done

echo "#####"
echo "Done!"

# Start the forwarder
cd scripts
echo "Stopping forwarder"
./stop_forwarder.sh