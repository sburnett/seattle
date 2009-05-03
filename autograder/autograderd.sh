#!/bin/sh


# ip address and port number of the computer where you're running everything
server_ip = "128.208.3.86"
server_port ="8090"


# name of log for output and errors
autograder_log="autograder_log.log"


arg_for_www= "$server_ip:$server_port"


./emulab/built/autograder_runner.py > &> $autograder_log  &
./www/manage.py runserver $arg_for_www > &>$autograder_log &