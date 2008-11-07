import traceback
from settings import *
#import manage
#import control.models as models
from control.models import User,Donation,Vessel,VesselMap,Share,VesselPorts,pop_key
from django.db import transaction
#import django.db.models as models
import django.core.exceptions as exceptions
import sys

def __get_guser__(donor_pubkey):
    '''
    returns user object based on the donor_pubkey, None on error
    '''
        
    try:
        return User.objects.get(donor_pubkey=donor_pubkey)
# this is equivalent to:
#    for u in User.objects.all():
#        print u.donor_pubkey
#        print (u.donor_pubkey == donor_pubkey)
    except exceptions.ObjectDoesNotExist:
        return None
    
def lookup_node(node_pubkey):
    try:
        node = Donation.objects.get(pubkey=node_pubkey)
    except exceptions.ObjectDoesNotExist:
        return None
    return node

def get_donor_keys():
    '''
    returns all the donor keys known
    '''
    users = User.objects.all()
    return [user.donor_pubkey for user in users]

def get_new_keys():
    '''
    returns a never used key (that will never be re-used)
    '''
    return pop_key()

def get_donor_privkey(pubkey):
    '''
    returns the donor's private key based on the pubkey
    '''
    u = __get_guser__(pubkey)
    if u is None:
        return None
    return u.donor_privkey

def create_update_node(node,node_info,donor_pubkey):
    '''
    takes a node_rec (Node instance obj) -- this can be None if no
    Node exists yet, node_info dictionary of values for ndoe, and
    dono_pubkey (so that we can match a new Donation record to an
    existing User record
    '''
    if node is None:
        # build new record
        guser = __get_guser__(donor_pubkey)
        if guser == None:
            raise Exception, "create_update_node: couldn't find donor with key string " + donor_pubkey
    
        node = Donation(user=guser,
                        pubkey=node_info['nodeid'],
                        ip = node_info['ip'],
                        port = node_info['port'],
                        status = node_info['status'],
                        version = node_info['version'],
                        owner_pubkey = node_info['owner_pubkey_str'],
                        owner_privkey = node_info['owner_privkey_str'])
    else:
        node.version = node_info['version']
        node.ip = node_info['ip']
        node.port = node_info['port']
        node.status = node_info['status']
    # save record
    node.save()
    return node

@transaction.commit_manually
def add_node_vessels(node,newstatus,vlist,vextra):
    '''
    Take's a node object and updates its status to newstatus, and adds
    all vessels in vlist and vextra as extra vessel. This is all done
    as a transaction.

    NOTE: in case of error in this function, use:
    transaction.rollback(); return False;
    '''
    print "in add_node_vessels"
    print "newstatus: ", newstatus
    print "VLIST: ", vlist
    print "VEXTRA: ", vextra

    try:
        node.status = newstatus
        node.save()
        # create the vessel records
        for (vname,vports) in vlist:
            v_rec = Vessel(donation = node,
                           name = vname,
                           status = "Initialized",
                           extra_vessel = False)
            v_rec.save()
            # create the vessel->port mapping for all ports assigned to this vessel
            for vport in vports:
                vport_rec = VesselPorts(vessel = v_rec, port = vport)
                vport_rec.save()
            
        # handle the extra (leftover) vessel
        vextra_rec = Vessel(donation = node,
                            name = vextra[0],
                            status = 'Initialized',
                            extra_vessel = True)
        vextra_rec.save()
        # create the vessel->port mapping for all ports assigned to this vessel
        for vport in vextra[1]:
            vport_rec = VesselPorts(vessel = vextra_rec, port = vport)
            vport_rec.save()
            
    except:
        traceback.print_exc()
        transaction.rollback()
        sys.exit()
        return False
    else:
        # success
        transaction.commit()
    return True

def update_node(node,newstatus):
    '''
    Takes a Node instance, and newstatus string. Updates the node's
    status and save the node.
    '''
    node.status = newstatus
    # note: timestamp updated on save()
    node.save()

if __name__ == '__main__':
    owner_key_str = '102581760161525849299480945390773462604452516673727153784436170616998785707093 828932698601553000080805048876997096119480280205665028530494046780633311955857068025674724327917536303134469749169449682860787080843248925875229718762166573070303171801656742580803907000114678479476569028271760705524370153555002217325596530079500410486609590403866179677127524204126433713843094372680813899'
    donor_privkey = get_donor_privkey(owner_key_str)
    donor_privkey = get_donor_privkey(owner_key_str+"1")
    print
    print "looking for: \n", owner_key_str
    print donor_privkey
    #print DATABASE_ENGINE
    #print User.objects.filter(port=9112)
    #lookup_donor(9112)
