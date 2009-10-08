#!/bin/bash

cd `dirname $0`

svn up trunk

python run_all_tests.py
