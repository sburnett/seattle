"""
<Program Name>
  share_operations.repy

<Started>
  February 13th, 2009

<Author>
  Ivan Beschastnikh

<Purpose>
  Encapsulate all functionality related to sharing between GENI users

<ToDo>

"""

import random
import time

from geni.control import vessel_flow
from geni.control.models import Share, VesselMap

def get_vcount_available(geni_user):
    return geni_user.vcount_base + geni_user.vcount_via_shares + geni_user.vcount_via_donations

def get_percent_usage(geni_user):
    # TODO: replace this with geni_user.num_acquired_vessels instead
    vcount_used = VesselMap.objects.filter(user = geni_user).count()
    vcount_available = get_vcount_available(geni_user)
    print "get_percent_usage: vcount used %i, and vcount_available %i"%(vcount_used, vcount_available)
    if vcount_available == 0:
        # error
        print "ERROR in share_operations.get_percent_usage() : vcount_available is 0"
        return 0
    return int((vcount_used * 1.0 / vcount_available * 1.0) * 100.0)


def edit_user_share(geni_user, geni_user_to_share_with, percent):
    """
    <Purpose>
    <Arguments>
    <Exceptions>
    <Side Effects>
    <Returns>
    """
    shares = Share.objects.filter(from_user = geni_user, to_user = geni_user_to_share_with)
    if shares.count == 0:
        return False, "No shares found between %s and %s"%(geni_user.www_user.username,
                                                           geni_user_to_share_with.www_user.username)
    share = shares[0]
    
    if percent == 0:
        # delete the share
        print "deleting user share"
        share.delete()
        return True, ""

    print "modifying user share to have percent ", str(percent)
    # modify the share
    share.percent = percent
    share.save()
    return True, ""


def create_user_share(geni_user, geni_user_to_share_with, percent):
    """
    <Purpose>
    <Arguments>
    <Exceptions>
    <Side Effects>
    <Returns>
    """
    
    shares = Share.build_shares(False)
    if vessel_flow.link_will_form_loop(shares, geni_user, geni_user_to_share_with):
        return False, "Cannot add a share that will create a sharing cycle"
    
    s =  Share (from_user = geni_user,
                to_user   = geni_user_to_share_with,
                percent   = percent)
    s.save()

    shares = Share.build_shares(False)
    pshares = Share.build_shares(True)
    base_vessels = Share.get_base_vessels()
    credits_from, vessels_from_shares = vessel_flow.flow_credits_from_roots(shares, pshares, base_vessels)

    print "new vessels_from_shares: "
    print vessels_from_shares
    
    for node, vcount in vessels_from_shares.items():
        print "updating node: ", node, type(node)
        print "with value: ", int(vcount)
        node.vcount_via_shares = int(vcount)
        node.save()
        
    return True, ""
