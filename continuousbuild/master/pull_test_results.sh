#!/usr/bin/env bash

# This script is intended to be run from the continuous build "master". That
# is, the system that can ssh into each of the continuous build machines and
# collect the continuous build output from each system so that it's all in one
# place.

DESTDIR=/home/continuousbuild/public_html

RSYNC_OPTIONS="--archive --delete"

rsync $RSYNC_OPTIONS testbed-opensuse:output/ $DESTDIR/linux
rsync $RSYNC_OPTIONS testbed-freebsd:output/ $DESTDIR/bsd

