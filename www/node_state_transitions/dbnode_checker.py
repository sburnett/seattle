"""
<Program Name>
  dbnode_checker.py

<Started>
  Februrary 28, 2008

<Author>
  ivan@cs.washington.edu
  Ivan Beschastnikh

<Purpose>
  Iterates through nodes in the GENI database, and checks the node
  state for consistency with the database. It _never_ changes the
  node, but instead changes the database to make the two consistent.

<Usage>
  Run from the command line without any args:
  $ python dbnode_checker.py

<ToDo>
  Right now the script iterates over the entire list of Donation
  records in the geni db. However, most records are duplicates (by
  IP). This means that the script connects multiple times to the same
  machine, when it only needs to connect once. This can be remedied by
  (1) grouping donations by IP and iterating through IPs and (2) when
  updating state of a node IP -- we update all of its records --
  i.e. we update the one with the pubkey we located to the most recent
  data, and we make the others inactive. Note that to accomplish this,
  the program structure has to be modified, and more complex db ops
  must be added
"""

import sys
import traceback
from django.db import transaction

import repyhelper
from repyportability import *
repyhelper.translate_and_import("nmclient.repy") #include nmclient.repy
repyhelper.translate_and_import("parallelize.repy") #include parallelize.repy

import genidb  # db api
import loggingrepy # circular logging to a file

def handle_donation(donation):
    """
    <Purpose>
        This function takes a donation record, connects to the node
        specified by the donation, and updates the db record depending
        on what it finds -- e.g. whether it can connect to the node,
        and what kind of host key the node has.

    <Arguments>
        donation : Donation model record corresponding to the node to
        check

    <Exceptions>
        None.

    <Side Effects>
        Connects to the node, and might modify the database Ddonation
        record

    <Returns>
        None
    """
    print time.ctime(), "Processing donation: ", donation
    
    host = donation.ip
    port = int(donation.port)

    thisnmhandle = None
    try:
        thisnmhandle = nmclient_createhandle(host, port)
        retdict = nmclient_getvesseldict(thisnmhandle)
        nodeID = rsa_publickey_to_string(retdict['nodekey'])
    except Exception, e:
        # close the handle on any error...
        print time.ctime(), "Exception in processing donation ", donation, ":", e
        traceback.print_exc(file=sys.stdout)
        genidb.handle_inactive_donation(donation)
    else:
        if donation.pubkey != nodeID:
            print time.ctime(), "Detected an active donation with key [%s..] != key in db [%s..] -- making inactive"%(nodeID[:10], donation.pubkey[:10])
            donation.epoch = 0
            donation.active = 0
        else:
            print time.ctime(), "Detected active donation", donation
            donation.epoch = genidb.DEFAULT_EPOCH_COUNT
            donation.active = 1
        donation.save()
    finally:
        if thisnmhandle != None:
            nmclient_destroyhandle(thisnmhandle)
    return

def handle_donations_parallel(donations):
    """
    <Purpose>
        Parallelizes the execution of handle_node (above) on a list of
        donation records.
        
    <Arguments>
        donations : a list of Donation model objects to process

    <Exceptions>
        None.

    <Side Effects>
        Spawn some number of threads that call handle_donation()

    <Returns>
        None
    """
    # We'll use a single thread to make this not really parallelized while we
    # are dealing with potential bugs among the node state transition scripts.
    num_threads = 1
    
    print "Running node checks parallelized using " + str(num_threads) + " thread(s)."

    try:
      phandle = parallelize_initfunction(donations, handle_donation, num_threads)
    except ParallelizeError, e:
      print time.ctime(), traceback.format_exc()

    # wait for handle_donation threads to finish
    while not parallelize_isfunctionfinished(phandle):
      sleep(1.0)
            
    resultdict = parallelize_getresults(phandle)
    
    parallelize_closefunction(phandle)

    # print any exceptions that might have occurred in the threads
    for donation, exception_str in resultdict['exception']:
      print time.ctime(), "handle_donation(%s) raised Exception: %s"%(donation, exception_str)
        
    return



def handle_donations_non_parallel(donations):
    """
    <Purpose>
        Processes donations in a sequential fashion (non-parallel)

    <Arguments>
        donations : a list of Donation model objects to process

    <Exceptions>
        None.

    <Side Effects>
        Calls handle_donation on each donation objects

    <Returns>
        None
    """
    for donation in donations:
        handle_donation(donation)
    return



def main():
    """
    <Purpose>
        Main loop of the db_checker script. This is a daemon script,
        so this function never returns. It grabs the current Donation
        records from the database, and checks them via
        handle_donation() for consistency with the database. It then
        sleep and repeats.

    <Arguments>
        None.

    <Exceptions>
        None.

    <Side Effects>
        Database is modified according to the Donation node state.

    <Returns>
        Never returns (daemon).
    """
    # to parallelize execution or not
    parallelize = True
    
    # loop forever    
    while True:
      
      # Grab all donation node records from the db.
      # Using list(queryset) forces evaluation of the query and returns a list.
      # This is largely because we can't pass a QuerySet to the call to 
      # handle_donations_parallel because it expects a list that it can pass to
      # parallelize_initfunction directly.
      # Of course, the nodes might have been changed in the database before the
      # call to handle_donation is actually made. We need to be careful with
      # that. This script didn't consider this before so we'll just wait for
      # the rewrite of these scripts to deal with that (e.g. lock node,
      # query db for fresh data about the node, do checks and update db, unlock node).
      donations = list(genidb.get_nodes())

      print time.ctime(), "Starting loop through " + str(len(donations)) + " nodes."
      
      # handle the donation records either in parallel or not
      if parallelize:
        handle_donations_parallel(donations)
      else:
        handle_donations_non_parallel(donations)
  
      # this is an essential hack to make django not use internal models caching:
	    # http://www.mail-archive.com/django-users@googlegroups.com/msg14826.html
      try:
        transaction.commit()
      except transaction.TransactionManagementError:
        pass
          
      # Sleep a few minutes just to make sure we don't hit any nodes too
      # frequently if there is something wrong with the script or the database.
      print time.ctime(),  "Finished loop through " + str(len(donations)) + " nodes. Sleeping a bit."
      sleep(5 * 60)
        
	
  
  
  
if __name__ == '__main__':
  logfn = "log.dbnode_checker"
  # set up the circular logger (at least 50 MB buffer)
  loggerfo = loggingrepy.circular_logger(logfn, 50*1024*1024)

  # redirect standard out / error to the circular log buffer
  sys.stdout = loggerfo
  sys.stderr = loggerfo
  print "logging output to " + str(logfn)
  main()
