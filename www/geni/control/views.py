from django.http import Http404
import datetime
from models import User,Donation,Vessel,VesselMap,Share
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response, get_object_or_404
from django.views.generic.simple import direct_to_template
from django.contrib.auth.decorators import login_required
#from django.core.exceptions import ObjectDoesNotExist
import sys
import forms

def validate_guser(request):
    try:
        geni_user = User.objects.get(www_user = request.user)
        return geni_user,True
    except User.DoesNotExist:
        # this should never happen if the user registered -- show server error of some kind
        ret = HttpResponse("User registration for this user is incomplete [auth records exists, but geni user profile is absent], please contact seattle-help@cs.washington.edu.")
        return ret,False

@login_required()
def donations(request):
    ret,success = validate_guser(request)
    if not success:
        return ret
    geni_user = ret

    mydonations = Donation.objects.filter(user = geni_user)
    myshares = Share.objects.filter(from_user = geni_user)
    share_form = forms.AddShareForm()
    return direct_to_template(request,'control/donations.html', {'geni_user' : geni_user, 'donations' : mydonations, 'shares' : myshares, 'share_form' : share_form})

@login_required()
def used_resources(request):
    ret,success = validate_guser(request)
    if not success:
        return ret
    geni_user = ret

    myvessels = VesselMap.objects.filter(user = geni_user)
    return direct_to_template(request,'control/used_resources.html', {'geni_user' : geni_user, 'vessels' : myvessels})

@login_required()
def user_info(request):
    ret,success = validate_guser(request)
    if not success:
        return ret
    geni_user = ret

    return direct_to_template(request,'control/user_info.html', {'geni_user' : geni_user})
    
@login_required()
def add_share(request):
    ret,success = validate_guser(request)
    if not success:
        return ret
    geni_user = ret
    
    if not request.method == 'POST':
        return main_user(request,geni_user)
    
    form = forms.AddShareForm(request.POST)
    form.set_user(geni_user)
    if form.is_valid():
        # commit to db
        s = Share(from_user=geni_user,to_user=form.cleaned_data['username'],percent=form.cleaned_data['percent'])
        # DEBUG
        s.save()
        form = None
    return main_user(request,geni_user,form)


def __dl_key__(request,pubkey=True):
    ret,success = validate_user(request)
    if not success:
        return ret
    geni_user=ret

    if pubkey:
        key = geni_user.pubkey
    else:
        key = geni_user.privkey
        
    response = HttpResponse(key, mimetype='text/plain')
    response['Content-Disposition'] = 'attachment; filename=%s.txt'%(request.user.username)
    return response

@login_required()
def dl_pubkey(request):
    return __dl_key__(request,True)

@login_required()
def dl_privkey(request):
    return __dl_key__(request,False)
