"""
<Program Name>
  accounts/views.py

<Started>
  October, 2008

<Author>
  ivan@cs.washington.edu
  Ivan Beschastnikh

<Purpose>
  Defines view functions that handle HTTP requests

  This file contains view functions for the control application which
  are called whenever a url is matched in geni.urls. These
  functions always take an HTTP request object, and return an HTTP
  response object, which is sometimes generated automatically by
  referencing a template via direct_to_template() and other
  django shorthands.

  For more information on views in django see:
  See http://docs.djangoproject.com/en/dev/topics/http/views/
"""

import django as django
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.contrib.auth import authenticate, login
import django.contrib.auth as auth
from django.views.generic.simple import direct_to_template
from django.contrib.auth.forms import AuthenticationForm
from django.core.urlresolvers import reverse
from django.conf import settings

from geni.control.models import User
import geni.accounts.forms as forms




def register(request):
    """
   <Purpose>
      Generate the user registration page HTTP response object

   <Arguments>
      request:
         An HTTP request object

   <Exceptions>
      Returns exceptions when the DBMS connection is
      unavailable.

   <Side Effects>
      Registers a new user in the GENI database with fields specified
      by the HTML registration form.

   <Returns>
      HTTP response object representing the server's respond to registration
      
   <FixMe>
      Would want to add validation of user email, and other features to here
    """
    if request.method == 'POST':
        form = forms.UserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            txt_pubkey = ""
            if 'pubkey' in request.FILES:
                file = request.FILES['pubkey']
                if file.size > 2048:
                    return HttpResponse("Public key too large, file size limit is 2048 bytes")
                txt_pubkey = file.read()
                
            print "TXT_PUBKEY IS:", txt_pubkey    
            if form.cleaned_data['gen_upload_choice'] == 2 and txt_pubkey == "":
                return HttpResponse("Enter a public key")

            # this saves the user's record to the database
            new_user = form.save()

            # this creates and saves the geni user in the database
            geni_user = User(www_user = new_user, affiliation=form.cleaned_data['affiliation'], pubkey=txt_pubkey, privkey="")
            geni_user.save_new_user()
            
            return show_login(request, 'accounts/login.html',
                              {'msg' : "Username %s has been successfully registered."%(new_user)})
    else:
        form = forms.UserCreationForm()
    return direct_to_template(request,'accounts/register.html', {'form' : form})




def login_redirect(request):
    """
   <Purpose>
      Return an HTTP redirection object that will redirect the user to
      the GENI login page.

   <Arguments>
      request:
         An HTTP request object

   <Exceptions>
      None

   <Side Effects>
      Redirects the user that issues the HTTP request to the login page.

   <Returns>
      HTTP redirection response object
    """
    return HttpResponseRedirect('/' + settings.URL_PREFIX + "accounts/login")





def login(request, simplelogin=False, msg=""):
    """
   <Purpose>
      Logs the user in by verifying their username/password. Checks if
      the user's browser supports cookies, and if it does then it sets
      up a persistent session for the user via cookies.
      
   <Arguments>
      request:
         An HTTP request object

   <Exceptions>
      None

   <Side Effects>
      Depending on the login success, might redirect the user to the
      login page or redirect them to the profile page (see control/)

   <Returns>
      HTTP response object that represents 
    """
    if simplelogin:
        ltemplate = 'accounts/simplelogin.html'
    else:
        ltemplate = 'accounts/login.html'
        
    if request.method == 'POST':
        form = AuthenticationForm(request.POST)
        if not request.session.test_cookie_worked():
            request.session.set_test_cookie()
            return show_login(request, ltemplate, {'err' : "Please enable your cookies and try again."}, form)

        if request.POST.has_key('jsenabled') and request.POST['jsenabled'] == 'false':
            return show_login(request, ltemplate, {'err' : "Please enable javascript and try again."}, form)

        user = authenticate(username=request.POST['username'], password=request.POST['password'])
        if user is not None:
            if user.is_active:
                # NOTE: not sure why login() without auth doesn't work
                auth.login(request, user)
                #try:
                    # only clear out the cookie if we actually authenticate and login ok
                try:
                    request.session.delete_test_cookie()
                except:
                    pass

                # Login successful!
                # Redirect to a success page.
                return HttpResponseRedirect(reverse("profile"))
            else:
                # Return a 'disabled account' error message
                return show_login(request, ltemplate, {'err' : "This account has been disabled."}, form)

        # Return an 'invalid login' error message.
        return show_login(request, ltemplate, {'err' : "Wrong username or password."}, form)

    return show_login(request, ltemplate, {})


def show_login(request, ltemplate, template_dict, form = None):
    if form == None:
        # initial page load
        form = AuthenticationForm()
        # set test cookie, but only once -- remove it on login
        #if not request.session.test_cookie_worked():
        request.session.set_test_cookie()
    template_dict['form'] = form
    return direct_to_template(request,ltemplate, template_dict)


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
    return direct_to_template(request,'accounts/help.html', {})
    
                              


def simplelogin(request):
    """
    <Purpose>
        Used to show a very simple login page (used for inclusion in Seattle Wiki)

    <Arguments>
        request:
            An HTTP request object

    <Exceptions>
        None.

    <Side Effects>
        None.

    <Returns>
        An HTTP response object that represents the simple login page on
        succes. A redirect to a login page on error.
    """
    return login(request, simplelogin=True)
    
                              


