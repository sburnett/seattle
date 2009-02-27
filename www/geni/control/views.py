"""
<Program Name>
  control/views.py

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

  For more information on views in django see:
  See http://docs.djangoproject.com/en/dev/topics/http/views/

  Multiple functions in this file contain the @login_required()
  decorator which enforces the HTTP connection to the browser to have
  a valid cookie that was established at login time:
  http://docs.djangoproject.com/en/dev/topics/auth/#the-login-required-decorator
"""

import sys
import forms
import datetime
import random

from django.utils import simplejson
from django.http import Http404
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response, get_object_or_404
from django.views.generic.simple import direct_to_template
from django.contrib.auth.decorators import login_required

from models import User, Donation, Vessel, VesselMap, Share
from resource_operations import acquire_resources, release_resources
import share_operations
from db_operations import pop_key

############################################# Private helper functions


def __validate_guser__(request):
    """
   <Purpose>
      Private helper function. Looks up and returns request.user in
      the geni database. This is used to verify that the user is a
      real user in the database and to retrieve a user's (ww-user)
      record.

   <Arguments>
      request:
         An HTTP request object that contains 'user' as an object

   <Exceptions>
      Returns exceptions when the DBMS connection is
      unavailable. Returns an exception when request has no user
      object

   <Side Effects>
      None.

   <Returns>
      (ret, bool) where bool indicates success of the lookup. If bool
      is True then ret is a User object. If bool is False then ret
      contains an HttpResponseRedirect object that redirect a user to
      the login page
      
   <FixMe>
      Add a check for whether request.user actually exists. If 
      it does not then we want to tell the user to register
    """
      
    try:
        geni_user = User.objects.get(www_user = request.user)
        return geni_user,True
    except User.DoesNotExist:
        ret = HttpResponseRedirect("/geni/accounts/login")
        return ret, False



def __dl_key__(request,pubkey=True):
    """
    <Purpose>
      Private helper function. Constructs an HttpResponse object that
      enables the user to download their public or private key.

    <Arguments>
      request:
         An HTTP request object that contains 'user' as an object
      pubkey:
         Boolean indicating whether the request is for a public key
         (True) or a private key (False)

    <Exceptions>
      None.?

    <Side Effects>
      None.

    <Returns>
      An HttpResponse object on success, otherwise if the user could
      not be found in the database then returns the Redirect object
      retured by __validate_guser__()
    """

    # retrieve the ww-user record for the request
    ret,success = __validate_guser__(request)
    if not success:
        return ret
    geni_user=ret

    if pubkey:
        # request is for a public key
        key = geni_user.pubkey
        extension = "publickey"
    else:
        # else request is for a private key
        key = geni_user.privkey
        extension = "privatekey"

    # create a response object that enables the user to download the requested key
    response = HttpResponse(key, mimetype='text/plain')
    response['Content-Disposition'] = 'attachment; filename=' + str(request.user.username) + '.' + str(extension)
    return response

#############################################
# Functions called to generate specific pages. Each requires a user to be logged in
#############################################

########################## Functions dealing with the donation page

@login_required()
def donations(request,share_form=None):
    """
    <Purpose>
        TODO : Under Construction -- Constructs a user's donations
        page (with shares)

    <Arguments>
        request:
            An HTTP request object
        share_form:
            Share object to use as the adding shares form on the page

    <Exceptions>
       None?

    <Side Effects>
       None.

    <Returns>
        An HTTP response object that represents the donations page on
        succes. A redirect to a login page on error.

    <Note>
        This method requires the request to represent a valid logged
        in user. See the top-level comment about the @login_required()
        decorator to achieve this property.
    """
    
    ret,success = __validate_guser__(request)
    if not success:
        return ret
    geni_user = ret

#    if share_form == None:
        # build a new add share form if none is supplied to us
#        share_form = forms.AddShareForm()
            
#    mydonations = Donation.objects.filter(user = geni_user)
#    myshares = Share.objects.filter(from_user = geni_user)
    
#    donations_to_me = []
#    has_donations_from_others = (len(donations_to_me) != 0)
#    has_donations = (len(mydonations) != 0)
#   has_shares = (len(myshares) != 0)
    
    return direct_to_template(request,'control/mygeni.html', {})
                              # {'geni_user' : geni_user,
#                                'has_donations' : has_donations,
#                                'donations' : mydonations, 
#                                'donations_to_me' : donations_to_me,
#                                'has_donations_from_others' : has_donations_from_others,
#                                'shares' : myshares,
#                                'has_shares' : has_shares,
#                                'share_form' : share_form})





@login_required()
def del_share(request):
    """
    <Purpose>
        Used to remove some of the user's shares.

    <Arguments>
        request:
            An HTTP request object

    <Exceptions>
       None? 

    <Side Effects>
        Deletes some subset of a user's Share records in the db.

    <Returns>
        An HTTP response object that represents the donations page on
        succes. A redirect to a login page on error.
    
    <Note>
        This method requires the request to represent a valid logged
        in user. See the top-level comment about the @login_required()
        decorator to achieve this property.

    <ToDo>
        1. Have a Share form for validating user input
        2. Generate a message for the user on success\failure of
           deleting the user's share(s).
    """
    # the request must be via a POST method
    if not request.method == 'POST':
        return donations(request)

    # validate user
    ret,success = __validate_guser__(request)
    if not success:
        return ret
    geni_user = ret

    # extract shares for this user
    myshares = Share.objects.filter(from_user = geni_user)
    for s in myshares:
        # check each share for whether it was requested for deletion by the user
        if request.POST.has_key('deleteshare_' + str(s.to_user.www_user.username)):
            s.delete()

    # return the donations page
    return donations(request)



    
@login_required()
def new_share(request):
    """
    <Purpose>
        Used to add new Share records for a user

    <Arguments>
        request:
            An HTTP request object
            
    <Exceptions>
       None?

    <Side Effects>
       Creates new Share records for a user in the db.

    <Returns>
        An HTTP response object that represents the donations page on
        succes. A redirect to a login page on error.

    <Note>
        This method requires the request to represent a valid logged
        in user. See the top-level comment about the @login_required()
        decorator to achieve this property.

    <Todo>
        1. Generate a msg for the user on success\failure
    """
    # the request must be via a POST method
    if not request.method == 'POST':
        return donations(request)

    # validate user
    ret,success = __validate_guser__(request)
    if not success:
        return ret
    geni_user = ret

    # construct the AddShareForm from request's POST args
    share_form = forms.AddShareForm(request.POST)
    # specify the user directly
    share_form.set_user(geni_user)
    if share_form.is_valid():
        # check for validity and commit request to GENI db:
        # create new Share for the user
        s = Share(from_user=geni_user,to_user=share_form.cleaned_data['username'],percent=share_form.cleaned_data['percent'])
        # save the new Share record
        s.save()
        share_form = None
    # return the donations page
    return donations(request,share_form)

########################## Functions dealing with the used resources page



@login_required()
def used_resources(request, get_form=False, action_explanation="", remove_explanation="", action_summary=""):
    """
    <Purpose>
        Constructs a user's used resources page.

    <Arguments>
        request:
            An HTTP request object            
        get_form:
            Get resources form used to acquire new resources by the user
        action_explanation:
           Explanation of the action to get resources by the user
        remove_explanation:
           Explanation of the result of the remove (free) resources action by the user
        action_summary:
            Summary of the user's acuisition of resources action

    <Exceptions>
        None?

    <Side Effects>
        None.

    <Returns>
        An HTTP response object that represents the used resources
        page on succes. A redirect to a login page on error.

    <Note>
        This method requires the request to represent a valid logged
        in user. See the top-level comment about the @login_required()
        decorator to achieve this property.

    <ToDo>
        1. Show shared used vessels for a user
    """
    # validate user
    ret,success = __validate_guser__(request)
    if not success:
        return ret
    geni_user = ret

    # generate a new 'get resources' form if none is supplied
    if get_form is False:
        get_form = forms.gen_get_form(geni_user)

    # shared vessels that are used by others but which belong to this user (TODO)
    shvessels = []

    # this user's used vessels
    my_vessels = VesselMap.objects.filter(user = geni_user).order_by('expiration')

    # return the used resources page constructed from a template
    return direct_to_template(request,'control/myvessels.html',
                              {'geni_user' : geni_user,
                               'num_vessels' : len(my_vessels),
                               'my_vessels' : my_vessels,
                               'sh_vessels' : shvessels,
                               'get_form' : get_form,
                               'action_explanation' : action_explanation,
                               'remove_explanation' : remove_explanation,
                               "action_summary" : action_summary})




@login_required()
def del_resource(request):
    """
    <Purpose>
        Used to release a resource the user acquired. Removes the
        record of the resource acquisition from the database.

    <Arguments>
        request:
            An HTTP request object
            
    <Exceptions>
        None?

    <Side Effects>
        Releases a previously acquired resources for a user

    <Returns>
        An HTTP response object that represents the used resources
        page on succes. A redirect to a login page on error.

    <Note>
        This method requires the request to represent a valid logged
        in user. See the top-level comment about the @login_required()
        decorator to achieve this property.

    <ToDo>
        1. Create a django form class for resource release
    """
    # the request must be via a POST method
    if not request.method == 'POST':
        return used_resources(request)

    # validate user    
    ret,success = __validate_guser__(request)
    if not success:
        return ret
    geni_user = ret

    # iterate through all the user's acquired resources and delete
    # those which are in the requests' POST args
    myresources = VesselMap.objects.all()
    remove_explanation = ""
    for r in myresources:
        if request.POST.has_key('delresource_' + str(r.id)):
            ret = release_resources(geni_user, r.id, False)
            remove_explanation = "Removed resource " + str(ret)
            
    if remove_explanation == "":
        remove_explanation = "Problem removing resource"

    # return the used resources page
    return used_resources(request,remove_explanation=remove_explanation)


@login_required()
def del_all_resources(request):
    """
    <Purpose>
        Used to release all resources acquired by a user

    <Arguments>
        request:
            An HTTP request object

    <Exceptions>
        None?

    <Side Effects>
        Releases all resources curently acquired by a user

    <Returns>
        An HTTP response object that represents the used resources
        page on succes. A redirect to a login page on error.

    <Note>
        This method requires the request to represent a valid logged
        in user. See the top-level comment about the @login_required()
        decorator to achieve this property.

    <Todo>
        1. Better unification with the above del_resource() function

    """
    # the request must be via a POST method
    if not request.method == 'POST':
        return used_resources(request)

    # validate user    
    ret,success = __validate_guser__(request)
    if not success:
        return ret
    geni_user = ret
    release_resources(geni_user, None, True)

    # return the used resources page
    return used_resources(request,remove_explanation="Removed all resources")




@login_required()
def get_resources(request):
    """
    <Purpose>
        Used by a user to acquire more Seattle resources.

    <Arguments>
        request:
            An HTTP request object
            
    <Exceptions>
        None?

    <Side Effects>
        Acquires new resources for a user (making them unavailable for other users)

    <Returns>
        An HTTP response object that represents the used resources
        page on succes. A redirect to a login page on error.
        
    <Note>
        This method requires the request to represent a valid logged
        in user. See the top-level comment about the @login_required()
        decorator to achieve this property.
    """

    # the request must be via a POST method
    if not request.method == 'POST':
        print "request.method is not POST"
        return used_resources(request)
    
    # validate user        
    ret,success = __validate_guser__(request)
    if not success:
        print "user invalid"
        return ret
    geni_user = ret

    action_explanation = ""
    get_form = forms.gen_get_form(geni_user,request.POST)
    if get_form is None:
        print "get_form is None"
        return used_resources(request, get_form, action_explanation=action_explanation)
    
    action_summary = ""
    if get_form.is_valid():
        # if the acquisition form is valid
        action_explanation = "" #get_form.cleaned_data['env']
        # acquire the requested resource
        env_type = get_form.cleaned_data['env']
        print "ENV_TYPE : " +  str(env_type)
        success,ret = acquire_resources(geni_user, int(get_form.cleaned_data['num']), env_type)

        # deserealize the returned value of the acquisition
        if success:
            num_acquired,action_explanation,action_summary = ret
        else:
            action_explanation,action_summary = ret
        print "acquire_resources returned: "
        print action_summary
        print action_explanation

    # have used_resources generate the updated get_form form
    return used_resources(request,get_form=False,
                          action_explanation=action_explanation,
                          action_summary=action_summary)




########################## Functions dealing with the user info page
    
@login_required()
def user_info(request,info=""):
    """
    <Purpose>
        Constructs the user info page.

    <Arguments>
        request:
            An HTTP request object            
        info:
            Used to display an information message at the top of the page

    <Exceptions>
        None?

    <Side Effects>
        None.

    <Returns>
        An HTTP response object that represents the user info
        page on succes. A redirect to a login page on error.

    <Note>
        This method requires the request to represent a valid logged
        in user. See the top-level comment about the @login_required()
        decorator to achieve this property.
    """
    # validate user
    ret,success = __validate_guser__(request)
    if not success:
        return ret
    geni_user = ret
    #return direct_to_template(request,'control/user_info.html',
    #                          {'geni_user' : geni_user,
    #                           'info' : info })
    return direct_to_template(request,'control/profile.html',
                              {'geni_user' : geni_user,
                               'info' : info})



    
@login_required()
def del_priv(request):
    """
    <Purpose>
        Used by the user to delete their own private key in order to
        make it more secure. The key is generated for those users who
        desire a new key to be generated and is kept up to this point.

    <Arguments>
        request:
            An HTTP request object
            
    <Exceptions>
        None?

    <Side Effects>
        Deletes the user's private key from the GENI db.

    <Returns>
        An HTTP response object that represents the user info page
        succes. A redirect to a login page on error.

    <Note>
        This method requires the request to represent a valid logged
        in user. See the top-level comment about the @login_required()
        decorator to achieve this property.
    """
    # the request must be via a POST method
    if not request.method == 'POST':
        return user_info(request)

    # validate user
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

    # return the user info page
    return user_info(request, info=del_msg)




@login_required()
def dl_pub_key(request):
    """
    <Purpose>
        Used by the user to download their own public donation key
        maintained by the GENI db

    <Arguments>
        request:
            An HTTP request object
            
    <Exceptions>
        None?

    <Side Effects>
        None

    <Returns>
        An HTTP response object that contains a file attachment that
        will allow the user to save the key file from the browser.

    <Note>
        This method requires the request to represent a valid logged
        in user. See the top-level comment about the @login_required()
        decorator to achieve this property.
    """
    # the request must be via a POST method
    if not request.method == 'POST':
        return user_info(request)
    return __dl_key__(request,True)




@login_required()
def dl_priv_key(request):
    """
    <Purpose>
        Used by the user to download their own public donation key
        maintained by the GENI db    

    <Arguments>
        request:
            An HTTP request object
            
    <Exceptions>
        None?

    <Side Effects>
        None

    <Returns>
        An HTTP response object that contains a file attachment that
        will allow the user to save the key file from the browser.

    <Note>
        This method requires the request to represent a valid logged
        in user. See the top-level comment about the @login_required()
        decorator to achieve this property.
    """
    # the request must be via a POST method
    if not request.method == 'POST':
        return user_info(request)
    return __dl_key__(request,False)




@login_required()
def gen_new_key(request):
    """
    <Purpose>
        Used by the user to generate a new public-private donation key
        pair.

    <Arguments>
        request:
            An HTTP request object

    <Exceptions>
        None.

    <Side Effects>
        Generates a new set of donation keys for a user, and updates
        the GENI db with the new keys.

    <Returns>
        An HTTP response object that represents the user info page
        succes. A redirect to a login page on error.

    <Note>
        This method requires the request to represent a valid logged
        in user. See the top-level comment about the @login_required()
        decorator to achieve this property.
    """
    # the request must be via a POST method
    if not request.method == 'POST':
        return user_info(request)

    # validate user
    ret,success = __validate_guser__(request)
    if not success:
        return ret
    geni_user = ret

    # generate a new key pair
    if geni_user.gen_new_key():
        info = "New public-private key pair generated"
    else:
        info = "Failed to generate a new public-private key pair (server error)"

    # return the generated user info page
    return user_info(request,info=info)


########################## Functions dealing with the getdonations page

@login_required()
def getdonations(request):
    """
    <Purpose>
        Shows a page where a user can download installers for their donations

    <Arguments>
        request:
            An HTTP request object

    <Exceptions>
        None.

    <Side Effects>
        None.

    <Returns>
        An HTTP response object that represents the getdonations page on
        succes. A redirect to a login page on error.
    """
    # validate user        
    ret,success = __validate_guser__(request)
    if not success:
        return ret
    geni_user = ret

    return direct_to_template(request,'control/getdonations.html', {'username' : geni_user.www_user.username})

########################## Functions dealing with Ajax pages

#### Ajax helper functions

def __jsonify(data):
    json = simplejson.dumps(data)
    return HttpResponse(json, mimetype='application/json')


def __validate_ajax(request):
    ret, success = __validate_guser__(request)
    if not success:
        return __jsonify({"success" : False, "error" : "could not validate your identity"}), False
    geni_user = ret

    # validate that the request is a POST method
    if not request.method == u'POST':
        return __jsonify({"success" : False, "error" : "request must be a POST method"}), False
    
    return geni_user, True


#### Ajax entrance functions

@login_required()
def ajax_getshares(request):
    ret, success = __validate_guser__(request)
    if not success:
        return __jsonify({"success" : False, "error" : "could not validate your identity"})
    geni_user = ret

    # retrieve all shares for the geni_user
    shares = share_operations.get_user_shares(geni_user)
    print "get_user_shares returned: "
    print shares

    # sort the shares according to their percent
    def share_compare(a, b):
        return cmp(a['percent'], b['percent'])
    shares.sort(share_compare)
    print "sorted shares: "
    print shares

    # sort shares into two lists: shares above threshold limit and
    # below threshold limit (for nice display on page)
    share_thresh = 10
    shares_above_thresh = []
    shares_below_thresh = []
    for share in shares:
        if share['percent'] > share_thresh:
            shares_above_thresh.append(share)
        else:
            shares_below_thresh.append(share)

    # calculate the share for 'me'
    geni_user_percent_used = share_operations.get_percent_usage(geni_user)
    geni_user_record = [{'username' : "Me", 'percent' : geni_user_percent_used}]
    
    ret = [shares_above_thresh, shares_below_thresh, geni_user_record]
    return __jsonify(ret)


@login_required()
def ajax_editshare(request):
    ret, success = __validate_ajax(request)
    if not success:
        return ret
    geni_user = ret

    form = forms.EditShareForm(request.POST)
    form.set_user(geni_user)
    if not form.is_valid():
        return __jsonify({"success" : False, "error" : form.get_errors_as_str()})
        
    percent = form.cleaned_data['percent']
    username = form.cleaned_data['username']

    success, str_err = share_operations.edit_user_share(geni_user,  form.shared_with_guser, percent)
    return __jsonify({"success" : success, "error" : str_err})



@login_required()
def ajax_createshare(request):
    ret, success = __validate_ajax(request)
    if not success:
        return ret
    geni_user = ret

    add_form = forms.AddShareForm(request.POST)
    add_form.set_user(geni_user)
    if not add_form.is_valid():
        return __jsonify({"success" : False, "error" : add_form.get_errors_as_str()})
        
    percent = add_form.cleaned_data['percent']
    username = add_form.cleaned_data['username']

    success, str_err = share_operations.create_user_share(geni_user, add_form.shared_with_guser, percent)
    return __jsonify({"success" : success, "error" : str_err})




@login_required()
def ajax_getcredits(request):
    ret, success = __validate_ajax(request)
    if not success:
        return ret
    geni_user = ret

    # NOTE: total percentage of percent_credits must be 100%
    percent_credits, total_vessels = share_operations.get_user_credits(geni_user)
    
    print "get_user_credits returned: "
    print percent_credits
    print total_vessels

    credits = []
    for guser, percent in percent_credits:
        if guser == geni_user:
            geni_user_record = [{'username' : "Me", 'percent' : percent}]
            continue

        credits.append({'username' : str(guser),
                        'percent' : percent})
    
    # sort the credits list according to their percent
    def credit_compare(a, b):
        return cmp(a['percent'], b['percent'])
    credits.sort(credit_compare)
    print "sorted credits: "
    print credits

    # sort credits into two lists: credits above threshold limit and
    # below threshold limit (for nice display on page)
    credit_thresh = 10
    credits_above_thresh = []
    credits_below_thresh = []
    for credit in credits:
        if credit['percent'] > credit_thresh:
            credits_above_thresh.append(credit)
        else:
            credits_below_thresh.append(credit)

    ret = [credits_above_thresh, credits_below_thresh, geni_user_record]
    return __jsonify(ret)



@login_required()
def ajax_getvessels(request):
    ret, success = __validate_ajax(request)
    if not success:
        return ret
    geni_user = ret


    get_form = forms.gen_get_form(geni_user,request.POST)
    if get_form is None:
        print "get_form is None"
        return __jsonify({"success" : False, "error" : "User cannot acquire any more vessels"})

    if not get_form.is_valid():
        return __jsonify({"success" : False, "error" : get_form.get_errors_as_str()})        
        
    action_explanation = ""
    # acquire the requested resource
    env_type = get_form.cleaned_data['env']
    print "ENV_TYPE : " +  str(env_type)
    success,ret = acquire_resources(geni_user, int(get_form.cleaned_data['num']), env_type)
    
    # deserealize the returned value of the acquisition
    if not success:
        num_acquired,action_explanation,action_summary = ret
        return __jsonify({"success" : False, "error" : action_summary})

    action_explanation,action_summary = ret
    print "acquire_resources returned: "
    print action_summary
    print action_explanation

    # ret = {"success" : True, "error" : "", 'mypercent' : 20, "vessels" : [{"vesselid" : "vid1", "status" : "ok!", "expiresin" : "24 hours!"}]}
    # {"success" : False, "error" : "Failed to acquire vessels", 'mypercent' : 20, "vessels" : []}
    return __jsonify({"success" : True, "error" : action_summary})

    


########################## Functions dealing with non-interactive pages (e.g. Help page or construction page)

@login_required()
def construction(request):
    """
    <Purpose>
        Used in case of website construction.

    <Arguments>
        request:
            An HTTP request object

    <Exceptions>
        None.

    <Side Effects>
        None.

    <Returns>
        An HTTP response object that represents the user info page
        succes. A redirect to a login page on error.
    """
    return direct_to_template(request,'control/construction.html', 
                              {'msg' : 'The GENI website is down for development work. Please come again soon.'})



@login_required()
def help(request):
    """
    <Purpose>
        Used to show the help page

    <Arguments>
        request:
            An HTTP request object

    <Exceptions>
        None.

    <Side Effects>
        None.

    <Returns>
        An HTTP response object that represents the help page on
        succes. A redirect to a login page on error.
    """
    return direct_to_template(request,'control/help.html', {})
    
                              
