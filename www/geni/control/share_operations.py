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

from models import Share


def get_user_shares(geni_user):
    """
    <Purpose>
    <Arguments>
    <Exceptions>
    <Side Effects>
    <Returns>
    """
    myshares = Share.objects.filter(from_user = geni_user)
    ret = []
    for share in myshares:
        ret.append({'username' : share.to_user.www_user.username,
                    'percent' : int(share.percent)})
    return ret

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
        share.delete()
        return True, ""

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
    s =  Share (from_user = geni_user,
                to_user   = geni_user_to_share_with,
                percent   = percent)
    s.save()
    return True, ""
