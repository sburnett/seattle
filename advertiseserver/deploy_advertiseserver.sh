#!/bin/bash

TRUNK_DIR=$1
DEPLOY_TO_DIR=$2

if [ -z $TRUNK_DIR ] || [ -z $DEPLOY_TO_DIR ]; then
  echo "Usage: ./deploy_advertiseserver.sh trunk_location deploy_dir"
  exit 1
fi

if [ ! -d $TRUNK_DIR ]; then
  echo "TRUNK_DIR doesn't exist: $TRUNK_DIR"
  exit 1
fi

if [ -d $DEPLOY_TO_DIR ]; then
  backupname=$DEPLOY_TO_DIR.bak.`date +%s`
  echo "Backing up $DEPLOY_TO_DIR as $backupname"
  mv $DEPLOY_TO_DIR $backupname || exit 1
fi

echo "Making directory $DEPLOY_TO_DIR"
mkdir $DEPLOY_TO_DIR || exit 1

echo "Copying files to $DEPLOY_TO_DIR. Expect a few messages about omitting directories."
cp $TRUNK_DIR/advertiseserver/* $DEPLOY_TO_DIR/
cp $TRUNK_DIR/repy/* $DEPLOY_TO_DIR/
cp $TRUNK_DIR/seattlelib/* $DEPLOY_TO_DIR/
cp $TRUNK_DIR/nodemanager/* $DEPLOY_TO_DIR/

echo "repypp'ing mix files"
cd $DEPLOY_TO_DIR
python repypp.py servicelogger.mix servicelogger.py
python repypp.py advertiseserver.mix advertiseserver.py

echo "Done."
echo "Use the following commands to start the advertise server:"
echo "#########################################"
echo "cd $DEPLOY_TO_DIR"
echo "python repy.py restrictions.advertiseserver advertiseserver.py >> log.stdout 2>> log.stderr < /dev/null"
echo "#########################################"

