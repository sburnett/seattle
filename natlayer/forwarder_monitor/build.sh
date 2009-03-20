#############################
# RJ
# March 20, 2009
# Setup and instructions for testing...


#################
# Part 1: Setup
###############

cd ../.. # change to trunk

mkdir foo
python preparetest.py foo
cp natlayer/forwarder_monitor/* foo


######################
# Part 2: instructions
################

# Now you should:
# (1) cd foo
# (2) go to internet browser + grab nodes from GENI
# (3) replace port 63111 in forwarder_rpc.py with your GENI port
# (4) python seash.py
# (5) ... loadkeys, setup 
# (6) upload forwarder_rpc.py
# (7) start forwarder_rpc.py # on all nodes
# (8) open new terminal
# (9) cd foo
# (10) python nat_forwarder_monitor.py #  finally run locally

# You should see:
#Added targets: 128.208.1.179:1224:v10
#Added targets: 128.208.1.116:1224:v12
#Added targets: 128.208.1.108:1224:v14
#Added targets: 128.208.1.150:1224:v10
#Added targets: 128.208.1.163:1224:v12
#True
#['128.208.1.179:1224:v10', '128.208.1.116:1224:v12', '128.208.1.108:1224:v14', '128.208.1.150:1224:v10', '128.208.1.163:1224:v12']
#current status of 128.208.1.179:1224:v10 => Started
#current status of 128.208.1.116:1224:v12 => Started
#current status of 128.208.1.108:1224:v14 => Started
#current status of 128.208.1.150:1224:v10 => Started
#current status of 128.208.1.163:1224:v12 => Started
