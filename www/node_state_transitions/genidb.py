"""
<Program Name>
  genidb.py

<Started>
  October 31, 2008

<Author>
  ivan@cs.washington.edu
  Ivan Beschastnikh

<Purpose>
  Provides a narrow interface to the GENI database.

  The interface provides functions to create nodes/vessels, to update
  a node, and to lookup a node record.

<Usage>
  Import this module as usual, but to work, you should have the
  PYTHONPATH setup to find control.models and you should have
  DJANGO_SETTINGS_MODULE defined. Example:
  
  export PYTHONPATH=$PYTHONPATH:/home/ivan/geni_private/:/home/ivan/
  export DJANGO_SETTINGS_MODULE='settings'

  
  NOTE: Some functions in this file use the
  @transaction.commit_manually decorator. This decorator changes the
  semantics of django database updates. More specifically, instead of
  automatically wrapping all operations that update the database into
  a transaction, django delegates transaction management to the
  programmer.

  If the function with this decorater modifies the database and does
  not call a transaction.rollback() or a transaction.commit() then
  django will raise an TransactionManagementError exception when the
  function returns.

  Therefore, it is safest to wrap any database updating functionally
  in such a function into a try/except/else and perform
  transaction.rollback() in the except block, and perform
  transaction.commit() in the else block.

  For more information on transaction management in django see:
  http://docs.djangoproject.com/en/dev/topics/db/transactions/
"""

# for time stuff
import time
# used for computing whether a VesselMap object is expired or not
import datetime
# useful for outputting the stack trace when there is a django exception
import traceback
# import django settings for this django project (geni)
from geni_private.settings import *
# import models that we use to interact with the geni database tables
from geni_production.geni.control.models import User, Donation, Vessel, VesselMap, Share, VesselPort, pop_key
# some functions will use transactions
from django.db import transaction
# django exceptions we might see
import django.core.exceptions as exceptions

DEFAULT_EPOCH_COUNT = 2

def __get_guser__(donor_pubkey_string):
    """
    <Purpose>
        A private function that returns the geni user database object
        associated with the user's donor public key.

    <Arguments>
        donor_pubkey_string (as string):
          the public key of the user

    <Exceptions>
        None.

    <Side Effects>
        None

    <Returns>
        Returns None if the geni user with the supplied donor key
        could not be found. Otherwise returns a geni user database
        object. The User class returned is defined in
        geni.control.models
    """
        
    try:
        return User.objects.get(donor_pubkey=donor_pubkey_string)
# this code is equivalent to:
#    for u in User.objects.all():
#        print u.donor_pubkey
#        print (u.donor_pubkey == donor_pubkey_string)
    except exceptions.ObjectDoesNotExist:
        return None

    
def get_nodes():
    """
    <Purpose>
        Returns the set of all donated node objects from the geni
        database

    <Arguments>
       None.

    <Exceptions>
        None.

    <Side Effects>
        None.

    <Returns>
        Returns a django queryset object containing all Donation records. This
        queryset object supports itteration and e.g. further filtering.

        For more information on django queryset objects, see:
        http://docs.djangoproject.com/en/dev/ref/models/querysets/
    """
    
    nodes = Donation.objects.all()
    return nodes

def lookup_donations_by_ip(nodeip):
    # this returns an array of potentially mulptiple donation objects that match nodeip in the database
    print time.ctime(), "looking up donations by nodeip ", nodeip
    donations = Donation.objects.filter(ip = nodeip)
    print time.ctime(), "found %i donations"%(donations.count())
    return donations

@transaction.commit_manually
def handle_inactive_donation(donation):
    if donation.active == 0:
        print time.ctime(), "Donation [%s] already inactive"%(donation) 
        return

    try:
        if donation.epoch == 0:
            print time.ctime(), "Donation [%s] epoch count is 0, making inactive"%(donation)
            vmaps = VesselMap.objects.filter(vessel_port__vessel__donation__exact = donation)
            print time.ctime(), "Deleting %i vesselmaps linked to this donation: %s"%(vmaps.count(), vmaps)
            for vmap in vmaps:
                vmap.delete()
            # TODO: need to update people's flow records here!!!
            donation.active = 0    
        else:
            donation.epoch -= 1
            print time.ctime(), "Donation [%s] inactive, epoch count is now %i"%(donation , donation.epoch)
        donation.save()    
    except:
        traceback.print_exc()
        transaction.rollback()
        raise
    else:
        # success
        transaction.commit()
    return True
    

def lookup_node(node_pubkey):
    """
    <Purpose>
        Returns a node object from the geni database corresponding to
        the node_pubkey host pubkey

    <Arguments>
        node_pubkey (as string):
          the node's host public key

    <Exceptions>
        None.

    <Side Effects>
        None.

    <Returns>
        If no node with host key is found in the database, returns
        None. Otherwise returns a node Donation object.

        The Donation class is defined in geni.control.models
    """
    
    try:
        node = Donation.objects.get(pubkey=node_pubkey)
    except exceptions.ObjectDoesNotExist:
        return None
    return node


def get_donor_keys():
    """
    <Purpose>
        Returns an array of all the donor keys (as string) known to geni

    <Arguments>
        None.

    <Exceptions>
        None.

    <Side Effects>
        None.

    <Returns>
        Returns an array of donor public keys (as strings)
    """
    
    users = User.objects.all()
    return [user.donor_pubkey for user in users]


def get_new_keys():
    """
    <Purpose>
        Supplies a never used public,privarte key pair that will never
        be re-used.

    <Arguments>
        None.

    <Exceptions>
        Might raise an exception if there are no more new keys in the database

    <Side Effects>
        None.

    <Returns>
        Returns an tuple of (publickey,privatekey) where both keys are strings
    """
        
    return pop_key()


def get_donor_privkey(pubkey):
    """
    <Purpose>
        Returns the donor's private key based on the public key

    <Arguments>
        pubkey (as string):
          The donor's public key

    <Exceptions>
        None.

    <Side Effects>
        None.

    <Returns>
        Returns the donor's private key (as string) that corresponds
        to the public key argument. Returns None if the donor's public
        key is not found in the database.
    """

    u = __get_guser__(pubkey)
    if u is None:
        return None
    return u.donor_privkey


def create_node(nodeid, ip, port, status, version, donor_pubkey_string):
    """
    <Purpose>
        Creates a new Donation record for a host with host public key
        nodeid, with node manager on ip:port, with status, and version
        as arguments. Associates the donation to a user based on the
        user's dono_pubkey public key.

    <Arguments>
        nodeid (string):
          The donation host's uniquely identifying public key

        ip (string):
          The ip of the donation host
    
        port:
          The port on which the node manager can be found

        status:
          The current status of the node
          
        version:
          The Seattle version on node
          
        donor_pubkey_string (string):
          The public key of the user donating the node

    <Exceptions>
        Exception:
          If the donor's public key could not be found in the database

    <Side Effects>
        Creates a new Donation record in the geni database for the node.

    <Returns>
        Returns the newly created Donation object corresponding to the
        donated host.
    """

    # look-up the user who is donating this node based on their public donor key
    guser = __get_guser__(donor_pubkey_string)
    if guser == None:
        raise Exception, "create_node: could not find donor with key string " + str(donor_pubkey_string)

    # get a new set of host-specific owner keys for this host
    (owner_pubkey_str, owner_privkey_str) = get_new_keys()

    # compute subnet from node's ip
    subnet = ''.join(ip.split('.')[:-1])
    
    # build new Donation record
    node = Donation(user=guser,
                    subnet = subnet,
                    pubkey=nodeid,
                    ip = ip,
                    port = port,
                    status = status,
                    version = version,
                    owner_pubkey = owner_pubkey_str,
                    owner_privkey = owner_privkey_str,
                    active = 0,
                    epoch = 0)
    
    # save and return the new node record
    node.save()
    return node


def update_node(node_obj, retdict, ip, port, status):
    """
    <Purpose>
        Updates the status, version, and node manager's ip:port for a node.
        
    <Arguments>
        node_obj (Donation object)
          The donation object to update

        version:
          The Seattle version with which to update the node record 
    
        ip:
          The node manger's ip with which to update the node record 

        port:
          The node manger's port with which to update the node record 
          
        status:
          The node status with which to update the node record 

    <Exceptions>
        None.

    <Side Effects>
        Updates fields of an existing node record in the database.

    <Returns>
        Always returns node_obj passed as argument
    """
    version = retdict['version']
    
    if node_obj.active == 0:
        print "updating node [%s] that was inactive -> active"%(node_obj)

    # update the Donation object's fields
    node_obj.version = version
    node_obj.ip = ip
    node_obj.port = port
    node_obj.status = status
    node_obj.active = 1
    node_obj.epoch = DEFAULT_EPOCH_COUNT
    # save node record 
    # NOTE: node's last seen timestamp is updated automatically on
    # call to save()
    node_obj.save()
    return node_obj


@transaction.commit_manually
def clear_node_vessels(node_obj):
    """
    <Purpose>
        Used to Remove all the vessels that correspond to a node. This
        can be performed whenever the node is moved into canonical
        state. This is done as a transaction.
        
    <Arguments>
        node_obj (Donation object)
          The donation object whose vessels are being nixed.

    <Exceptions> 
        Raises whatever exception raised by an offending
        error with removing corresponding records from the database.

    <Side Effects> 
        Removes VesselPort, VesselMap, and Vessel records from the
        database that correspond to the Vessels of the node object.

    <Returns>
        Returns True on success. If this function fails then it raises
        the Exception that caused the failure.
    
    NOTE: The use of @transaction.commit_manually decorator is
    explained at the top of this file.
    """

    print "in clear_node_vessels"
    try:
        # find all vessels corresponding to this node
        vessels = Vessel.objects.filter(donation = node_obj)
        print "removing vessels: " + str(vessels)
        for v in vessels:
            # delete all the vessel port entries
            vports = VesselPort.objects.filter(vessel = v)
            for vport in vports:
                # delete all the corresponding vessel map entries
                vmaps = VesselMap.objects.filter(vessel_port = vport)
                for vmap in vmaps:
                    vmap.delete()
                vport.delete()
            # delete the vessel record
            v.delete()
    except:
        traceback.print_exc()
        transaction.rollback()
        raise
    else:
        # success
        transaction.commit()
    return True


def get_expired_vesselmaps(): 
    """
    <Purpose>
        Used to find all assigned (mapped) vessels that have expired
        
    <Arguments>
        None.

    <Exceptions> 
        Raises whatever exception raised by an offending
        error when accessing the genidb

    <Side Effects> 
        None.

    <Returns>
        Returns array of VesselMap objects that are expired.
    """
    curr_time = datetime.datetime.now() 
    vmaps = VesselMap.objects.all() 
    ret_vmaps = []
    # iterate through all vmap objects and find those that are expired
    for vmap in vmaps: 
        if vmap.expiration <= curr_time: 
            ret_vmaps.append(vmap)
    # returns array of expired vessel map objects
    return ret_vmaps 

@transaction.commit_manually
def add_node_vessels(node_obj, newstatus, vlist, vextra, vextra_ports):
    """
    <Purpose> 
        Creates Vessel, VesselPort, and VesselMap objects
        corresponding to the vessels associated with the Donation
        object. This is done as a transaction.
            
    <Arguments>
        node_obj (Donation object):
          The donation object for which we are created new vessels
    
        newstatus:
          The new status of the node
          
        vlist:
          Vessel list of (vname,vports) tuples. Where vports is a list
          of vessel ports

        vextra:
          The vessel name of the extra (leftover vessel).

        vextra_ports:
          The ports numbers corresponding to the extra vessel.

    <Exceptions> 
        Raises whatever exception raised by an offending error with
        creating new records in the database corresponding to the node

    <Side Effects> 
        Creates Vessel, and VesselPort records in the database that
        correspond to the the node object.

    <Returns>
        Returns True on success. If this function fails then it raises
        the Exception that caused the failure.
    
    NOTE: The use of @transaction.commit_manually decorator is
    explained at the top of this file.
    """
    
    print "in add_node_vessels"
    print "newstatus: ", newstatus
    print "VLIST: ", vlist
    print "VEXTRA: ", vextra

    try:
        node_obj.status = newstatus
        node_obj.save()
        # create the new vessel records
        for (vname,vports) in vlist:
            v_rec = Vessel(donation = node_obj,
                           name = vname,
                           status = "Initialized",
                           extra_vessel = False)
            v_rec.save()
            # create the vessel->port mappings for all ports assigned to this vessel
            for vport in vports:
                vport_rec = VesselPort(vessel = v_rec, port = vport)
                vport_rec.save()

                
        # handle the extra (leftover) vessel specially
        vextra_rec = Vessel(donation = node_obj,
                            name = vextra,
                            status = 'Initialized',
                            extra_vessel = True)
        vextra_rec.save()
        # create the vessel->port mapping for all ports assigned to the extra vessel
        for vport in vextra_ports:
            vport_rec = VesselPort(vessel = vextra_rec, port = vport)
            vport_rec.save()
            
    except:
        traceback.print_exc()
        transaction.rollback()
        raise
    else:
        # success
        transaction.commit()
    return True


if __name__ == '__main__':
    print "new rand pub/priv key pair: "
    print pop_key()
#     owner_key_str = '102581760161525849299480945390773462604452516673727153784436170616998785707093 828932698601553000080805048876997096119480280205665028530494046780633311955857068025674724327917536303134469749169449682860787080843248925875229718762166573070303171801656742580803907000114678479476569028271760705524370153555002217325596530079500410486609590403866179677127524204126433713843094372680813899'
#     donor_privkey = get_donor_privkey(owner_key_str)
#     donor_privkey = get_donor_privkey(owner_key_str+"1")
#     print
#     print "looking for: \n", owner_key_str
#     print donor_privkey
#     #print DATABASE_ENGINE
#     #print User.objects.filter(port=9112)
#     #lookup_donor(9112)
