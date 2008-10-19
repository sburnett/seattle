import django as django
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.contrib.auth import authenticate, login
import django.contrib.auth as auth
from django.views.generic.simple import direct_to_template
from django.contrib.auth.forms import AuthenticationForm
import forms
from geni.control.models import User

def register(request):
    '''
    User registration page
    '''
    if request.method == 'POST':
        form = forms.UserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            txt_pubkey = ""
            if 'pubkey' in request.FILES:
                file = request.FILES['pubkey']
                if file.size > 2048:
                    return HttpResponse("Public key too large, file size limit is 2048 bytes")
                txt_pubkey = file.read()
            # this saves the user's record to the database
            new_user = form.save()
            # this creates and saves the geni user in the database
            geni_user = User(www_user = new_user, port=9112, affiliation=form.cleaned_data['affiliation'], pubkey=txt_pubkey, privkey="")
            geni_user.save_new_user()
            return HttpResponseRedirect("/geni/accounts/login/")
    else:
        form = forms.UserCreationForm()
    return direct_to_template(request,'accounts/register.html', {'form' : form})

def login(request):
    '''
    User login page
    '''
    ltemplate = 'accounts/login.html'
    err = ""
    if request.method == 'POST':
        form = AuthenticationForm(request.POST)
        if not request.session.test_cookie_worked():
            err = "Please enable your cookies and try again."
            request.session.set_test_cookie()
            return direct_to_template(request,ltemplate, {'form' : form, 'err' : err})
            
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
                #except:
                #    pass
                # Redirect to a success page.
                return HttpResponseRedirect("/geni/control/")
            else:
                # Return a 'disabled account' error message
                err = "This account has been disabled."
                return direct_to_template(request,ltemplate, {'form' : form, 'err' : err})
        else:
            # Return an 'invalid login' error message.
            err = "Wrong username or password."
            return direct_to_template(request,ltemplate, {'form' : form, 'err' : err})
    else:
        # initial page load
        form = AuthenticationForm()
        # set test cookie, but only once -- remove it on login
        #if not request.session.test_cookie_worked():
        request.session.set_test_cookie()
    return direct_to_template(request,ltemplate, {'form' : form, 'err' : err})

