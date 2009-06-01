"""
   Author: Justin Cappos

   Start Date: 29 May 2009

   Description:

   This is the database interface for the seattleGENI backend.   This module
   is used called by backend.py to interact with the database.
"""


# used for computing whether a VesselMap object is expired or not
import datetime

import time

# import django settings for this django project (geni)
from geni_private.settings import *
# import models that we use to interact with the geni database tables

# JAC: Where is geni_production?
#from geni_production.geni.control.models import User, Donation, Vessel, VesselMap, Share, VesselPort, pop_key
from geni.control.models import User, Donation, Vessel, VesselMap, Share, VesselPort, pop_key

# some functions will use transactions
from django.db import transaction
# django exceptions we might see
import django.core.exceptions as exceptions


import django.db

def init_database():
  """
    <Purpose>
      Initializes the database.   Must be called first.

    <Arguments>
      None.

    <Exceptions>
      It is possible for a Django / Database error to be thrown (which is fatal)

    <Side Effects>
      This function makes it so that we see any transactions that occur at the 
      time of the database read (instead of the time of the transaction).   
      This is necessary since none of our operations are transactional in 
      nature.   If we did not have this, the entire lifetime of our program 
      would be a single transaction

    <Returns>
      None.
  """
  django.db.connection.cursor().execute('set transaction isolation level read committed')


def _find_userobj_given_username(username):
  success, thisuserobj = User.get_guser_by_username(username)
  if not success:
    raise Exception("Cannot find entry for username '"+username+"'")
  return thisuserobj
  


def _find_donationobj_given_vesselname(vesselname):
  try:
    donationid, vesselid = vesselname.split(':')
  except Exception, e:
    raise Exception("Error splitting vesselname '"+str(e)+"'")

  donationobjlistlikeobj = Donation.objects.filter(pubkey=donationid)
  if len(donationobjlistlikeobj) == 0:
    raise Exception("Donation record for '"+vesselname+"' was not found.")
  elif len(donationobjlistlikeobj) > 1:
    raise Exception("Multiple donation records for '"+vesselname+"'.")

  donationobj = donationobjlistlikeobj[0]
  return donationobj


def _find_vesselobj_given_vesselname(vesselname):
  ip, port, vesselid = convert_vesselname_to_ipportid(vesselname)

  donationobj = _find_donationobj_given_vesselname(vesselname)
  
  # Now I just need the vessel object for this donation id...
  vesselobjlistlikeobj = Vessel.objects.filter(donation = donationobj).filter(name = vesselid)

  if len(vesselobjlistlikeobj) == 0:
    raise Exception("Vessel record for '"+vesselname+"' was not found.")
  elif len(vesselobjlistlikeobj) > 1:
    raise Exception("Multiple vessel records for '"+vesselname+"'.")

  vesselobj = vesselobjlistlikeobj[0]
  
  return vesselobj


def _get_vesselmapobjs_for_vesselname(vesselname):
  
  # get the vessel object...
  vesselobj = _find_vesselobj_given_vesselname(vesselname)

  # get all vesselport objects that correspond to this...
  vesselportobjlistlikeobj = VesselPort.objects.filter(vessel = vesselobj)

  retvesselmapobjlist = []
  for vesselportobj in vesselportobjlistlikeobj:
    for vesselmapobj in VesselMap.objects.filter(vessel_port = vesselportobj):
      retvesselmapobjlist.append(vesselmapobj)

  return retvesselmapobjlist
    


def write_vesselname_to_vesselmap(vesselname, username,VESSEL_EXPIRE_TIME_SECS= 60*60*4):
  """
    <Purpose>
      Writes an entry into the vesselmap
      This function is not meant to be called concurrently on the same
      vesselname.

    <Arguments>
      vesselname:
        The vessel to assign to the user.   The name is in the format:
        str(host public key):vesselid
      username:
        The user who will have a vesselmap entry created
      VESSEL_EXPIRE_TIME_SECS:
        The lifetime of the entry

    <Exceptions>
      Exception is raised when the call fails.   The string that is returned
        will give details as to why the call failed.
      ValueError or TypeError are raised when given invalid input.

    <Side Effects>
      None.

    <Returns>
      None.
  """

  # ensure this isn't already in use...
  if vesselname_is_in_vesselmap(vesselname):
    raise Exception("Vesselname '"+vesselname+"' already has an entry in the vesselmap and a write was requested!")
    

  # to start with, we need to check the vessel isn't in use and find the 
  # VesselPort object.   This is a long task...   

  # first, get the vesselobject ...
  vesselobj = _find_vesselobj_given_vesselname(vesselname)
    
  # I need the port from the user name to get the VesselPort from the Vessel
  userobj = _find_userobj_given_username(username)
  userport = userobj.port

  vesselportobjlistlikeobj = VesselPort.objects.filter(vessel = vesselobj).filter(port = userport)
  if len(vesselportobjlistlikeobj) == 0:
    raise Exception("Vesselport record for '"+vesselname+"' was not found.")
  elif len(vesselportobjlistlikeobj) > 1:
    raise Exception("Multiple vesselport records for '"+vesselname+"'.")

  vesselportobj = vesselportobjlistlikeobj[0]


  # create the new object...
  newvesselmapobj = VesselMap(vessel_port = vesselportobj, user = userobj, expiration = datetime.datetime.fromtimestamp(time.time() + VESSEL_EXPIRE_TIME_SECS))

  # and commit it to the database...
  newvesselmapobj.save()

    


def remove_vesselname_from_vesselmap(vesselname):
  """
    <Purpose>
      Removes the vesselmap for a vessel.
      This function is not meant to be called concurrently on the same
      vesselname.

    <Arguments>
      vesselname:
        The vessel to remove from vesselmaps.   The name is in the format:
        str(host public key):vesselid

    <Exceptions>
      Exception is raised when the call fails.   The string that is returned
        will give details as to why the call failed.   Examples include the
        non-existence of a vesselmap for this vessel, more than one vessel
        map for the vessel or a database error.

    <Side Effects>
      None.

    <Returns>
      None.
  """

  vesselmapobjlist = _get_vesselmapobjs_for_vesselname(vesselname)
  if len(vesselmapobjlist) == 0:
    raise Exception("Cannot remove nonexistent VesselMap for vessel '"+vesselname+"'")
  elif len(vesselmapobjlist) > 1:
    raise Exception("More than 1 VesselMap for vessel '"+vesselname+"'")

  vesselmapobj = vesselmapobjlist[0]
  vesselmapobj.delete()


  
def vesselname_is_in_vesselmap(vesselname):
  """
    <Purpose>
      Indicates if a vessel has a vesselmap.
      This function is not meant to be called concurrently on the same
      vesselname.

    <Arguments>
      vesselname:
        The vessel to check.   The name is in the format:
        str(host public key):vesselid

    <Exceptions>
      Exception is raised when the call fails.   The string that is returned
        will give details as to why the call failed.   (Perhaps by having
        multiple vesselmaps for the same vessel).

    <Side Effects>
      None.

    <Returns>
      True if a vesselmap exists for the vessel, False otherwise.
  """
  try:
    vesselmapobjlist = _get_vesselmapobjs_for_vesselname(vesselname)
  except Exception, e:
    if "Vessel record" in str(e) and "not found" in str(e):
      return False
    else: 
      raise
  else:
    if len(vesselmapobjlist) == 1:
      return True
    elif len(vesselmapobjlist) == 0:
      return False
    raise Exception("Multiple vesselmaps for vessel '"+vesselname+"'")


def get_ownerkeys_given_vesselname(vesselname):
  """
    <Purpose>
      Returns the keys for a vessel.

    <Arguments>
      vesselname:
        The vesselname for which we should get the keys.   The name is in the 
        format: str(host public key):vesselid

    <Exceptions>
      Exception is raised when the call fails (perhaps due to a bad vesselname).

    <Side Effects>
      None.

    <Returns>
      A tuple (publickeystring, privatekeystring)
  """

    
  donationobj = _find_donationobj_given_vesselname(vesselname)

  return (donationobj.owner_pubkey, donationobj.owner_privkey)


def convert_vesselname_to_ipportid(vesselname):
  """
    <Purpose>
      Takes a vesselname and returns the ip, port, and vesselid for this vessel

    <Arguments>
      vesselname:
        The vessel that is being inquired about.   The name is in the format:
        str(host public key):vesselid

    <Exceptions>
      Exception is raised when the call fails.   The string that is returned
        will give details as to why the call failed.

    <Side Effects>
      None.

    <Returns>
      A tuple (ip, port, vesselid).   For example: ('1,2,3,4',11111,'v32')
  """
  donationobj = _find_donationobj_given_vesselname(vesselname)
  try:
    donationid, vesselid = vesselname.split(':')
  except Exception, e:
    raise Exception("Error splitting vesselname '"+str(e)+"'")

  return donationobj.ip, donationobj.port, vesselid

