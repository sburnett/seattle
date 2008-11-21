"""
<Program Name>
  models.py

<Started>
  October, 2008

<Author>
  ivan@cs.washington.edu
  Ivan Beschastnikh

<Purpose>
  Defines view functions that handle HTTP requests

  This file contains view functions for the control application which
  are called whenever a url is matched in geni.control.urls. These
  functions always take an HTTP request object, and return an HTTP
  response object, which is sometimes generated automatically by
  referencing a template via direct_to_template() and other
  django shorthands.

  See http://docs.djangoproject.com/en/dev/topics/http/views/
"""

import sys
import forms
import datetime

from django.http import Http404
from models import User,Donation,Vessel,VesselMap,Share,pop_key,acquire_resources, release_resources
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response, get_object_or_404
from django.views.generic.simple import direct_to_template
from django.contrib.auth.decorators import login_required

def __validate_guser__(request):

    # TODO: add a check for whether request.user actually exists. If
    # it does not then we want to tell the user to register
    
    try:
        geni_user = User.objects.get(www_user = request.user)
        return geni_user,True
    except User.DoesNotExist:
        ret = HttpResponseRedirect("/geni/accounts/login")
        return ret, False

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

#######################################################

@login_required()
def donations(request,share_form=None):
    ret,success = __validate_guser__(request)
    if not success:
        return ret
    geni_user = ret

    if share_form == None:
        share_form = forms.AddShareForm()
            
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
def del_share(request):
    if not request.method == 'POST':
        return donations(request)
    
    ret,success = __validate_guser__(request)
    if not success:
        return ret
    geni_user = ret

    myshares = Share.objects.filter(from_user = geni_user)
    for s in myshares:
        if request.POST.has_key('deleteshare_%s'%(s.to_user.www_user.username)):
            s.delete()
            
    return donations(request)
    
@login_required()
def new_share(request):
    if not request.method == 'POST':
        return donations(request)

    ret,success = __validate_guser__(request)
    if not success:
        return ret
    geni_user = ret

    share_form = forms.AddShareForm(request.POST)
    share_form.set_user(geni_user)
    if share_form.is_valid():
        # commit to db
        s = Share(from_user=geni_user,to_user=share_form.cleaned_data['username'],percent=share_form.cleaned_data['percent'])
        s.save()
        share_form = None
        
    return donations(request,share_form)

#######################################################

def gen_get_form(geni_user,req_post=None):
    # max allowed resources this user may get
    donations = Donation.objects.filter(user=geni_user).filter(active=1)
    num_donations = len(donations)
    max_num = 10 * (num_donations + 1)
    
    # number of vessels already used by this user
    myvessels = VesselMap.objects.filter(user = geni_user)
    
    if len(myvessels) > max_num:
        max_num = 0
    else:
        max_num = max_num - len(myvessels)

    if max_num == 0:
        get_form = None
    else:
        get_vessel_choices = zip(range(1,max_num+1),range(1,max_num+1))
        get_form = forms.gen_GetVesselsForm(get_vessel_choices,req_post)
    return get_form

@login_required()
def used_resources(request,get_form=False,explanation="",explanation2="",summary=""):
    ret,success = __validate_guser__(request)
    if not success:
        return ret
    geni_user = ret

    if get_form is False:
        get_form = gen_get_form(geni_user)

    shvessels = []
    my_vessels = VesselMap.objects.filter(user = geni_user).order_by('expiration')
    #if explanation == "":
    #    explanation = "HELLO"
    return direct_to_template(request,'control/used_resources.html', {'geni_user' : geni_user, 'num_vessels' : len(my_vessels), 'my_vessels' : my_vessels, 'sh_vessels' : shvessels, 'get_form' : get_form, 'action_explanation' : explanation, 'remove_explanation' : explanation2, "action_summary" : summary})

@login_required()
def del_resource(request):
    if not request.method == 'POST':
        return used_resources(request)
    
    ret,success = __validate_guser__(request)
    if not success:
        return ret
    geni_user = ret

    myresources = VesselMap.objects.all()
    explanation2 = ""
    for r in myresources:
        if request.POST.has_key('delresource_%s'%(r.id)):
            ret = release_resources(geni_user, r.id, False)
            explanation2 = "Removed resource " + str(ret)
            
    if explanation2 == "":
        explanation2 = "Problem removing resource"
    
    return used_resources(request,explanation2=explanation2)

@login_required()
def del_all_resources(request):
    if not request.method == 'POST':
        return used_resources(request)
    
    ret,success = __validate_guser__(request)
    if not success:
        return ret
    geni_user = ret
    release_resources(geni_user, None, True)
    return used_resources(request,explanation2="Removed all resources")

@login_required()
def get_resources(request):
    if not request.method == 'POST':
        return used_resources(request)
    
    ret,success = __validate_guser__(request)
    if not success:
        return ret
    geni_user = ret

    explanation = ""
    get_form = gen_get_form(geni_user,request.POST)
    if get_form is None:
        return used_resources(request,get_form,explanation=explanation)
    
    summary = ""
    if get_form.is_valid():
        explanation = get_form.cleaned_data['env']
        ret = acquire_resources(geni_user, int(get_form.cleaned_data['num']), get_form.cleaned_data['env'])
        if ret[0] is True:
            dummy,num_acquired,explanation,summary = ret
        else:
            dummy,explanation,summary = ret
    return used_resources(request,get_form,explanation=explanation,summary=summary)

#######################################################
    
@login_required()
def user_info(request,info=""):
    ret,success = __validate_guser__(request)
    if not success:
        return ret
    geni_user = ret
    return direct_to_template(request,'control/user_info.html', {'geni_user' : geni_user, 'info' : info })
    
@login_required()
def del_priv(request):
    if not request.method == 'POST':
        return user_info(request)
    
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
    return user_info(request,info=del_msg)

@login_required()
def dl_pub_key(request):
    if not request.method == 'POST':
        return user_info(request)
    return __dl_key__(request,True)

@login_required()
def dl_priv_key(request):
    if not request.method == 'POST':
        return user_info(request)
    return __dl_key__(request,False)

@login_required()
def gen_new_key(request):
    if not request.method == 'POST':
        return user_info(request)
        
    ret,success = __validate_guser__(request)
    if not success:
        return ret
    geni_user = ret
    if geni_user.gen_new_key():
        info = "New public-private key pair generated"
    else:
        info = "Failed to generate a new public-private key pair (server error)"
    return user_info(request,info=info)
