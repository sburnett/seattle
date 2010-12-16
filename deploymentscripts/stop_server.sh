
python deploy_server_monitor.py kill
`ps -ef | grep deploy_server_monitor | grep -v grep | awk '{ if ($1 == "nsr") print $2 } ' | xargs kill -9 `