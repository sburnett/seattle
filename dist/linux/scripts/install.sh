#!/bin/sh
which_out=`which python`
if [ "$which_out" = "" ]; then
    echo seattle requires that python be installed on your computer.
    echo Please install python and try again.
else
    python install.py
fi
exit
