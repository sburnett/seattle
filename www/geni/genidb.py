from settings import *
#import manage
from control.models import User,Donation,Vessel,VesselMap,Share
import sys

def lookup_donor(_pubkey):
    try:
        # guser = User.objects.get(pubkey=_pubkey)
        guser = User.objects.get(port=_pubkey)
    except:
        print "Unable to find user in genidb with pubkey: %s"%(_pubkey)
        print "Unexpected error:", sys.exc_info()[0]
        return None
        
    donations = Donation.objects.filter(user=guser)
    return donations


if __name__ == '__main__':
    print DATABASE_ENGINE
    print User.objects.filter(port=9112)
    #lookup_donor(9112)
