#!/bin/bash
#
# Pre-process the three files

python ../seattlelib/repypp.py server.py rep_server.py
python ../seattlelib/repypp.py client.py rep_client.py
python ../seattlelib/repypp.py forwarder.py rep_forwarder.py
