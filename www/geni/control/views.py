from django.http import Http404
import datetime
from models import User,Donation,Vessel,VesselMap,Share
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response, get_object_or_404
from django.views.generic.simple import direct_to_template
from django.contrib.auth.decorators import login_required
#from django.core.exceptions import ObjectDoesNotExist
#import django.models as models
#from  django.db.models import Model
import sys


@login_required()
def main(request):
    try:
        #user = request.user.get_profile()
        geni_user = User.objects.get(www_user = request.user)
    except User.DoesNotExist:
        # TODO: except DoesNotExist -- where is this exception defined?
        geni_user = User(www_user = request.user, port=9112 , affiliation="UW")
        geni_user.save()

    mydonations = Donation.objects.filter(user = geni_user)
    myvessels = VesselMap.objects.filter(user = geni_user)
    myshares = Share.objects.filter(from_user = geni_user)
    return direct_to_template(request,'control/main.html', {'geni_user' : geni_user, 'donations' : mydonations, 'vessels' : myvessels, 'shares' : myshares})

    
