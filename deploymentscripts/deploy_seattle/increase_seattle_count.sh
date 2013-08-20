#!/bin/bash

rm /home/monzum/planetlab_node_tests/free_planetlab_nodes.txt

# Planetlab nodes.
python /home/monzum/planetlab_node_tests/run_parallel_node_script.py /home/monzum/planetlab_node_tests/planetlab_nodes.txt /home/monzum/planetlab_node_tests/pl_bash_scripts/free_pl_nodes.sh uw_seattle flibble  
python /home/monzum/planetlab_node_tests/run_parallel_node_script.py /home/monzum/planetlab_node_tests/free_planetlab_nodes.txt pl_bash_scripts/install_fresh_seattle.sh uw_seattle flibble 
python /home/monzum/planetlab_node_tests/run_parallel_node_script.py /home/monzum/planetlab_node_tests/planetlab_nodes.txt /home/monzum/planetlab_node_tests/pl_bash_scripts/start_seattle_pl.sh uw_seattle flibble
 python /home/monzum/planetlab_node_tests/run_parallel_node_script.py /home/monzum/planetlab_node_tests/planetlab_nodes.txt pl_bash_scripts/start_crond.sh uw_seattle flibble
sleep 10

rm /home/monzum/planetlab_node_tests/free_planetlab_nodes.txt

# Gpeni Nodes.

python /home/monzum/planetlab_node_tests/run_parallel_node_script.py /home/monzum/planetlab_node_tests/GpENI_ip.txt /home/monzum/planetlab_node_tests/pl_bash_scripts/free_pl_nodes.sh gpeni_seattle flibble
python /home/monzum/planetlab_node_tests/run_parallel_node_script.py /home/monzum/planetlab_node_tests/free_planetlab_nodes.txt /home/monzum/planetlab_node_tests/pl_bash_scripts/install_fresh_seattle.sh gpeni_seattle flibble
python /home/monzum/planetlab_node_tests/run_parallel_node_script.py /home/monzum/planetlab_node_tests/GpENI_ip.txt /home/monzum/planetlab_node_tests/pl_bash_scripts/start_seattle_pl.sh gpeni_seattle flibble
python /home/monzum/planetlab_node_tests/run_parallel_node_script.py /home/monzum/planetlab_node_tests/GpENI_ip.txt /home/monzum/planetlab_node_tests/pl_bash_scripts/start_crond.sh gpeni_seattle flibble
sleep 10

rm /home/monzum/planetlab_node_tests/free_planetlab_nodes.txt

# German nodes.

python /home/monzum/planetlab_node_tests/run_parallel_node_script.py /home/monzum/planetlab_node_tests/glab_hostname.txt /home/monzum/planetlab_node_tests/pl_bash_scripts/free_pl_nodes.sh glab_seattle_public flibble
python /home/monzum/planetlab_node_tests/run_parallel_node_script.py /home/monzum/planetlab_node_tests/free_planetlab_nodes.txt /home/monzum/planetlab_node_tests/pl_bash_scripts/install_fresh_seattle.sh glab_seattle_public flibble
python /home/monzum/planetlab_node_tests/run_parallel_node_script.py /home/monzum/planetlab_node_tests/glab_hostname.txt /home/monzum/planetlab_node_tests/pl_bash_scripts/start_seattle_pl.sh glab_seattle_public flibble
python /home/monzum/planetlab_node_tests/run_parallel_node_script.py /home/monzum/planetlab_node_tests/glab_hostname.txt /home/monzum/planetlab_node_tests/pl_bash_scripts/start_crond.sh glab_seattle_public flibble