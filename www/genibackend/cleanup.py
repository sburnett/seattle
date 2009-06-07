"""
   Author: Justin Cappos

   Start Date: 28 May 2009

   Description:

   This cleans up any vessels that shouldn't be assigned...
"""


# I need to get lock objects to handle concurrency and will use settimer for 
# running the cleanup thread...
from repyportability import *


import time


# import django settings for this django project (geni)
from geni_private.settings import *
# import models that we use to interact with the geni database tables
# JAC: Where is geni_production?
from geni.control.models import User, Donation, Vessel, VesselMap, Share, VesselPort, pop_key
# some functions will use transactions
from django.db import transaction
# django exceptions we might see
import django.core.exceptions as exceptions
import django.db

import DatabaseAPI
import NodeManagerAPI


# the list of vesselnames that need to be cleaned up before reuse...
cleanuplist = []

# need sys to flush output to stdout/stderr
import sys

def add_all_free_to_cleanup_list():
  # first get the donation object for this...
  for donationobj in Donation.objects.filter(active = True):
    pubkeyname = donationobj.pubkey

    # Now get all vessels for this
    for vesselobj in Vessel.objects.filter(donation = donationobj).filter(extra_vessel = False):
      vesselid = vesselobj.name

      vesselname = pubkeyname+":"+vesselid
      # Check to be sure it's not allocated...
      if DatabaseAPI.vesselname_is_in_vesselmap(vesselname):
        print "Entry exists for: "+vesselname
      else:
        cleanuplist.append(vesselname)
  


# private.   This will run forever and clean up vessels that we were asked
# to clean up

def _cleanup_vessels():

  while cleanuplist:

    count = 0.0

    # We'll do this forever...
    try:
      for vesselname in cleanuplist[:]:
        count = count + 1.0
        try:
          print time.time(),vesselname[-10:], "before database api", count / len(cleanuplist)
          sys.stdout.flush()
          # somehow get the key from the database...
          ownerpublickey, ownerprivatekey = DatabaseAPI.get_ownerkeys_given_vesselname(vesselname)
 
          print time.time(),vesselname[-10:], "before database api convert"
          sys.stdout.flush()
          try:
            vesselip, vesselport, vesselid = DatabaseAPI.convert_vesselname_to_ipportid(vesselname)
          except Exception, e:
            print "Horrible internal error!!! '"+str(e)+"'"
            exitall()

          print time.time(),vesselname[-10:], "Before change users"
          sys.stdout.flush()
          NodeManagerAPI.dosignedcall(vesselip, vesselport, ownerpublickey, ownerprivatekey, "ChangeUsers", vesselid, '')
          # clean up the vessel state
          print time.time(),vesselname[-10:], "Before reset vessel"
          sys.stdout.flush()
          NodeManagerAPI.dosignedcall(vesselip, vesselport, ownerpublickey, ownerprivatekey, "ResetVessel", vesselid)
        except Exception, e:
          print e
          continue
        cleanuplist.remove(vesselname)


    except Exception, e:
      print "cleanup: ",e
      pass

    print "-"*60
    print time.time(),len(cleanuplist)
    print "-"*60
    sys.stdout.flush()

    sleep(2)





def main():

  # give the database and node manager api a chance to init
  DatabaseAPI.init_database()
  NodeManagerAPI.init_nmapi()
  add_all_free_to_cleanup_list()
  _cleanup_vessels()



if __name__ == '__main__':
  main()
