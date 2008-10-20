from settings import *
#import manage
from control.models import User,Donation,Vessel,VesselMap,Share,pop_key
from django.db import transaction
import sys

# 1 day
EXPIRE_TIME_SECS = 86400

def __get_guser__(donor_pubkey):
    '''
    returns user object based on the donor_pubkey, None on error
    '''
    try:
        return User.objects.all.get(donor_pubkey=pubkey)
    except:
        return None
    
def lookup_node(node_pubkey):
    try:
        node = Donation.objects.get(pubkey=node_pubkey)
    except:
        print "Unable to find a donated node in genidb with pubkey: %s"%(node_pubkey)
        print "Error:", sys.exc_info()[0]
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
            return False
    
        node = Donation(user=guser,
                        pubkey=node_info[''],
                        ip = node_info['ip'],
                        port = node_info['port'],
                        status = node_info['status'],
                        version = node_info['version'],
                        owner_pubkey = node_info['owner_pubkey'],
                        ownerprivkey = node_info['owner_privkey'])
    else:
        node.version = node_info['version']
        node.ip = node_info['ip']
        node.port = node_info['port']
        node.status = node_info['status']
    # save record
    node.save()
    return True

@transaction.commit_manually
def add_node_vessels(node,newstatus,vlist,vextra):
    '''
    Take's a node object and updates its status to newstatus, and adds
    all vessels in vlist and vextra as extra vessel. This is all done
    as a transaction.

    NOTE: in case of error in this function, use:
    transaction.rollback(); return False;
    '''
    
    
    node.status = newstatus
    node.save()
    expire_time = time.time() + EXPIRE_TIME_SECS
    for v in vlist:
        vrec = Vessel(donation = node,
                      expiration = expire_time,
                      port = v['port'],
                      name = v['name'],
                      status = v['status'],
                      extra_vessel = False)
        vrec.save()
        
    vrec_extra = Vessel(donation = node,
                        expiration = expire_time,
                        port = vextra['port'],
                        name = vextra['name'],
                        status = vextra['status'],
                        extra_vessel = True)
    vrec_extra.save()
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
    print DATABASE_ENGINE
    print User.objects.filter(port=9112)
    #lookup_donor(9112)
