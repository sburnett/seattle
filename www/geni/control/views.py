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

def __validate_guser__(request):
    try:
        geni_user = User.objects.get(www_user = request.user)
        return geni_user,True
    except User.DoesNotExist:
        # this should never happen if the user registered -- show server error of some kind
        ret = HttpResponse("User registration for this user is incomplete [auth records exists, but geni user profile is absent], please contact seattle-help@cs.washington.edu.")
        return ret,False

def __dl_key__(request,pubkey=True):
    ret,success = __validate_guser__(request)
    if not success:
        return ret
    geni_user=ret

    if pubkey:
        key = geni_user.pubkey
        extension = "publickey"
    else:
        key = geni_user.privkey
        extension = "privatekey"
        
    response = HttpResponse(key, mimetype='text/plain')
    response['Content-Disposition'] = 'attachment; filename=%s.%s'%(request.user.username,extension)
    return response

@login_required()
def donations(request):
    ret,success = __validate_guser__(request)
    if not success:
        return ret
    geni_user = ret
    
    
    share_form = forms.AddShareForm()
    if request.method == 'POST' and request.POST.has_key('new_share'):
        share_form = forms.AddShareForm(request.POST)
        share_form.set_user(geni_user)
        if share_form.is_valid():
            # commit to db
            s = Share(from_user=geni_user,to_user=share_form.cleaned_data['username'],percent=share_form.cleaned_data['percent'])
            s.save()
            share_form = forms.AddShareForm()
            
    elif request.method == 'POST' and request.POST.has_key('update_shares'):
        myshares = Share.objects.filter(from_user = geni_user)
        for s in myshares:
            if request.POST.has_key('deleteshare_%s'%(s.to_user.www_user.username)):
                s.delete()
#             if request.POST.has_key('percent_%s'%(s.to_user.www_user.username)) and \
#                s.percent != request.POST['percent_%s']:
#                 s.percent = int(request.POST['percent_%s'])
            
    mydonations = Donation.objects.filter(user = geni_user)
    myshares = Share.objects.filter(from_user = geni_user)
    
    # TODO
    donations_to_me = []
    if len(donations_to_me) != 0:
        has_donations_from_others = 'True'
    else:
        has_donations_from_others = 'False'
    
    if len(mydonations) != 0:
        has_donations = 'True'
    else:
        has_donations = 'False'

    if len(myshares) != 0:
        has_shares = 'True'
    else:
        has_shares = 'False'
    return direct_to_template(request,'control/donations.html', {'geni_user' : geni_user, 'has_donations' : has_donations, 'donations' : mydonations, 
                                                                 'donations_to_me' : donations_to_me, 'has_donations_from_others' : has_donations_from_others,
                                                                 'shares' : myshares, 'has_shares' : has_shares, 'share_form' : share_form})

@login_required()
def used_resources(request):
    ret,success = __validate_guser__(request)
    if not success:
        return ret
    geni_user = ret

        
    # TODO: use vessel flow graph. for now a limit of 10 vessels per user
    myvessels = VesselMap.objects.filter(user = geni_user)
    if len(myvessels) > 10:
        print "ERROR : len(myvessels) > 10!"
        max_num = 0
    else:
        max_num = 10 - len(myvessels)

    get_vessel_choices = zip(range(1,max_num+1),range(1,max_num+1))
    get_form = forms.gen_GetVesselsForm(get_vessel_choices)
    
    if request.method == 'POST':
        # TODO
        get_form = forms.gen_GetVesselsForm(get_vessel_choices,req_post=request.POST)
        if get_form.is_valid():
            # commit to db and notify Seattle
            pass
        
    # TODO
    shvessels = []
    return direct_to_template(request,'control/used_resources.html', {'geni_user' : geni_user, 'my_vessels' : myvessels, 'sh_vessels' : shvessels, 'get_form' : get_form})

@login_required()
def user_info(request,msg=""):
    ret,success = __validate_guser__(request)
    if not success:
        return ret
    geni_user = ret
    return direct_to_template(request,'control/user_info.html', {'geni_user' : geni_user, 'msg' : msg })
    
@login_required()
def del_priv(request):
    ret,success = __validate_guser__(request)
    if not success:
        return ret
    geni_user = ret
    if geni_user.privkey == "":
        del_msg = "Private key has already been deleted"
    else:
        geni_user.privkey = ""
        geni_user.save()
        del_msg = "Private key successfully deleted"
    return user_info(request,msg=del_msg)

@login_required()
def dl_pub_key(request):
    return __dl_key__(request,True)

@login_required()
def dl_priv_key(request):
    return __dl_key__(request,False)
