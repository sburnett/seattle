"""
<Program Name>
  resource_operations.py

<Started>
  Feburary 4th, 2009

<Author>
  Ivan Beschastnikh
  Alper Sarikaya

<Purpose>
  Defines various functions to help manage the resources of vessels
  and donations.

<ToDo>
  ...

"""

import datetime
import time
import sys
import traceback

from django.db import connection
from django.db import transaction

from geni.control.models import User, VesselPort, VesselMap
#from geni.control.repy_dist.changeusers import changeusers
from geni.control.repy_dist.vessel_operations import release_vessels, acquire_lan_vessels, acquire_wan_vessels, acquire_rand_vessels

# 4 hours worth of seconds
VESSEL_EXPIRE_TIME_SECS = 14400

def create_vmaps(vessels, geni_user, pending_flag=False):
    """
    <Purpose>
      Creates the VesselMap class instances matching the vessels and
      saves them to the GENI database associated with the geni_user
    <Arguments>
      vessels:
        An array of vessels for which to create the VesselMap entries
      geni_user:
        An instance of class User to match on VesselMap instances
      pending_flag:
        An optional argument that when set true will instantiate a 
        temporary instance of a vmap entry (assumes a daemon is
        running around cleaning up expired pending vmaps)
    <Exceptions>
      None
    <Side Effects>
      Creates new vesselmap database entries
    <Returns>
      True on success, False on failure
    """
    expire_time = datetime.datetime.fromtimestamp(time.time() + 
                                                  VESSEL_EXPIRE_TIME_SECS)
    for v in vessels:
        # find the vessel port entry corresponding to this vessel and 
        # user's port
        vports = VesselPort.objects.filter(vessel = v).filter(port = geni_user.port)
        if len(vports) != 1:
            return False
        vport = vports[0]
        # create and save the new vmap entries
        print "create and save vmap ", time.time()


        vmap = None
        # alpers - if this is a temporary entry, save it as such
        if pending_flag:
            print "vmap: creating temp entry"
            vmap = VesselMap(vessel_port = vport, user = geni_user, 
                             expiration = str(expire_time), pending = 0,
                             time_acquired = datetime.datetime.fromtimestamp(time.time()))
        else:
            # we should check here if a vmap has already been made, but is 
            # pending:
            vmap = VeselMap.objects.filter(vessel_port = vport, 
                                           user = geni_user, pending = 1)
            if len(vmap) > 1:
                raise "should have only got one entry back, instead got " + \
                    "%d: %s" % (len(vmap), vmap)
          
            # if len == 1, then we've found an entry: activate it!
            if len(vmap) == 1:
                vmap = vmap[0]
                vmap.pending = 0
                # vmap.save()

            # no entry found, create a new one (should never really happen)
            else:
                print "*** a vmap was made from scratch, not from a " + \
                    "pending entry.."
                vmap = VesselMap(vessel_port = vport, user = geni_user, 
                                 expiration = str(expire_time))

        vmap.save()
        

        print "/create and save vmap ", time.time()
    return True



def release_resources(geni_user, resource_id, all):
    """
    <Purpose>
      Releases either all resources (vesselmaps) or some specific
      resource for a geni user.
    <Arguments>
      geni_user:
        instance of the User class indicating the geni user
      resource_id (int):
        indicates the specific vessel map record to delete
      all (boolean):
        if True then deletes all vessel maps for the user
    <Exceptions>
      Not sure.
    <Side Effects>
      Deletes some number of vessel map entries associated with the geni_user.
    <Returns>
      If all is False, returns a string representation of the vessel
      that was removed. Otherwise returns an empty string
    """

    ret = ""
    myresources = VesselMap.objects.filter(user=geni_user)

    # select the vessels from current resources based on all or specific
    # resource_id
    myvessels = []
    if all:
        for r in myresources:
            myvessels.append(r.vessel_port.vessel)
    else:
        for r in myresources:
            if r.id == resource_id:
                myvessels.append(r.vessel_port.vessel)
            
    # release the selected vessels
    resultdict = release_vessels(myvessels)

    # cycle through the results of releasing, make sure releasing succeeded
    # before modifying database/objects
    for vessel, (success, msg) in resultdict.iteritems():
        vmaps = VesselMap.objects.filter(vessel_port__vessel__exact = vessel)
        if vmaps.count() != 1:
            print "release_resources: got too many/little matches to specific vessel (%s) when releasing (count = %d); not releasing" % (vessel, vmaps.count())
            continue

        # if releasing did not succeed, don't bother modifying metadata
        if not success:
            print "release_resources: failed to changeusers to \"\", not releasing, reason: %s" % msg
            continue
        # if it did succeed, update state
        else:
            ret = str(vessel.donation.ip) + ":" + str(vessel.donation.port) + \
                ":" + str(vessel.name)
            vmaps[0].delete()
            geni_user.num_acquired_vessels -= 1

    return ret
            

@transaction.commit_manually    
def acquire_resources(geni_user, num, env_type):
    """
    <Purpose>
      Acquire num resources/vessels for usergeni_user of type env_type
      (LAN\WAN\Random).

    <Arguments>
      geni_user :
        A User class instance (see below) representing user for whom
        to acquire the vessels
      num :
        Number of vessels to acquire
      env_type :
        The type of vessel environment to acquire. Current support
        values are 1 : LAN, 2 : WAN, 3 : Random

    <Exceptions>
      None

    <Side Effects>
      Modifies the geni database to reflect new vessel
      assignments. Specifically, this function creates new VesselMap
      records and assigns vessels to users. This function also
      modifies vessel state by changing their user keys to geni_user's
      key.

    <Returns>
      bool, list where bool is True on success (some vessels
      acquired), False on failure (no vessels acquired). If bool is
      True then list is (acquired, explanation, summary) where
      acquired is the number of vesesls acquired, explanation is the
      detailed explanation of went on, and summary is a summary
      explanation of what went on. If bool is False then list is
      (explanation, summary) where explanation is a detailed
      explanation and summary is a summary explanation of why we
      failed.
    """
    explanation = ""
    summary = ""
    env_type_func_map = {1 : acquire_lan_vessels,
                         2 : acquire_wan_vessels,
                         3 : acquire_rand_vessels}
    try:
        num_available = geni_user.vessel_credit_remaining()
        if num > num_available:
            # user wants too much
            summary = "You do not have enough donations to acquire %d vessels"%(num)
            return False, (explanation, summary)

        # charge the user for requested resources
        geni_user.num_acquired_vessels += num

        if num == 1:
            acquire_func = acquire_rand_vessels
        else:
            acquire_func = env_type_func_map[int(env_type)]
        # attempt to acquire resources
        success, ret = acquire_func(geni_user, num)
        
        if not success:
            summary, explanation = ret
            explanation += "No more nodes available."
            transaction.rollback()
            return False, (explanation, summary)

        summary, explanation, acquired = ret
        ret = create_vmaps(acquired, geni_user)
        if not ret:
            release_vessels(acquired)
            raise "create_vmaps failed"
            

        #explanation += "There are  " + str(total_free_vessel_count) + " vessels free. Your port is available on " + str(len(vessels)) + " of them."
            
    except:
        transaction.rollback()
        # a hack to get the traceback information into a string by
        # printing to file and then reading back from file
        #traceback.print_tb(file=sys.stdout)
        summary += " Failed to acquire vessel(s). Internal Error. Please contact ivan@cs.washington.edu"
        summary += ''.join(traceback.format_exception(sys.exc_info()[0],sys.exc_info()[1],sys.exc_info()[2]))
        return False, (explanation, summary)
    else:
        transaction.commit()
        summary += " Acquired %d vessel(s). "%(num)
        return True, (num, explanation, summary)
