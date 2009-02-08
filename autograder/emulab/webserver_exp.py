import remote_emulab

# This is a very rough sample of what a client
# to the remote_emulab.py library will look like
#
# Everything below is hardcoded and is not intended
# to be executed (it will fail because it assumes a
# new and unique exp name).  It is just an exmaple 
# senerio. 

# if you want to run it and see it work, first you'll
# need to set up keys and your login for remote_emulab.py
# then just change exp below from "helloworld"+n to
# "helloworld"+(n+1) so that the name will be unique.
# You should probably be polite and permanately remove the
# the new exp from emulab when you are done.


import install_autograder
import sys


# SETUP SOME CONSTANTS

# specify the emulab proj name, this is always 'Seattle'
proj = "Seattle"


#specify the name of an ns file being used
mynsfn = "lan.ns"

def do_exp(simple_links):
  print "running exp with links" , simple_links
  # in seconds
  timeout = 45
  keyname = "autograder"
  server_port = 8080
  (server_hostname, server_ip) = simple_links[0]
  install_autograder.run_emulab_repy(server_hostname, keyname, timeout, 
                                     "server.repy", repy_argstring="server.repy %i"%(server_port))
  for (hostname, ip) in simple_links[1:]:
    install_autograder.run_emulab_repy(hostname, keyname, timeout, 
                                       "test.repy", 
                                       repy_argstring="test.repy %s %i"%(server_ip, server_port))
  # TODO: change this to polling the log
  # 15 seconds overhead
  sleep(60)
  logs = get_logs()
  print "NODE LOGS: ", logs
  return logs


def create_nstext(nsfile, args):
  # read the ns file into a string
  mynsfobj = open(mynsfn)
  mynsfilestr = mynsfobj.read()
  mynsfobj.close()
  mynsfilestr = mynsfilestr%(args)
  return mynsfilestr

def main(nstext, exp):
  # check the ns file for errors
  (passed,message) = remote_emulab.checkNS(nstext)

  if (not passed):
    print message
    print "checkNS failed, please fix the ns file and try again"
    return

  
  # start a new exp in non-batchmode
  print "starting a new exp..."
  remote_emulab.startexp(proj,exp,nstext)

  # wait for the exp to go active
  # by default times out in 10 minutes
  print "exp started, waiting for active..."
  remote_emulab.wait_for_active(proj,exp)

  #print "now active... getting links"
  links = remote_emulab.get_links(proj,exp)
  simple_links = remote_emulab.simplify_links(proj,exp,links)

  # do the experiment
  #do_exp(simple_links)
  

  #print "finished exp, swapping out"
  #remote_emulab.swapOUT(proj,exp)
  #print "swaped out"



def usage():
  # print usage
  print "python webserver_exp.py [expirament name] [# of nodes]"


if __name__ == "__main__":
  
  # check number of arguments, print usage if wrong
  if len(sys.argv) != 3:
    usage()
    sys.exit()


  exp = sys.argv[1]
  number_of_nodes = int(sys.argv[2])
  if (number_of_nodes < 2):
    print "number of nodes must be greater than 1"
    sys.exit()
  
  nstext = create_nstext(mynsfn, number_of_nodes)
  main(nstext, exp)
