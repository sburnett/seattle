"""
<Program>
  views.py

<Author>
  Jason Chen
  jchen@cs.washington.edu

<Started>
  September, 2009
  
<Purpose>
  Django view functions used in rendering the HTML view of the installer_creator.
"""
import hashlib
import time

from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.views.generic.simple import direct_to_template
from django.utils import simplejson


from installer_creator.common import builder
from installer_creator.common import validations 

INSTALLER_ID_LENGTH = 30


def installer_creator(request):
  # Flush the session dict, so new & returning users get a clean dict
  request.session.flush()

  return direct_to_template(request, 'mainpage.html', {})
  

def add_user(request):
  """
  <Purpose>
    This function is called via POST whenever the user clicks "Add" 
    on the page. The POST request contains the username and uploaded 
    key (if exists). If the user doesn't supply a key, then one is 
    generated for them.
    
    The keys are eventually stored in the user's SESSION, for later retrieval. 
  """
  if not request.method == 'POST':
    return HttpResponseRedirect(reverse("installer_creator"))
  
  if request.POST['action'] == 'adduser':
    #username = _standarize(request.POST['username'])
    username = request.POST['username']
    
    try:
      validations.validate_username(username)
    except validations.ValidationError:
      return HttpResponse("usernamebad")
    
    if username == "":
      return HttpResponse("usernameempty")
    
    key_dict = {}
    
    # check if the given username was previously entered
    if username in request.session:
      return HttpResponse("duplicateusername")
    
    if 'publickey' in request.FILES:
      # User uploaded a pubkey, read out of uploaded file and store into request dict
      pubkey_file = request.FILES['publickey']
      if pubkey_file.size > 2048:
        # NOTE: The JS parsing this response splits the below response by the
        # underscore symbol, and treats the latter half as the max file-size value
        # displayed in the user-side alert. If you change the above max file-size,
        # be sure you change the response appropriately as well. 
        return HttpResponse("pubkeytoolarge_2048")
      
      read_pubkey = pubkey_file.read()
      
      try:
        validations.validate_pubkey_string(read_pubkey)
      except validations.ValidationError:
        return HttpResponse("pubkeybad")
      
      key_dict = {'pubkey' : read_pubkey, 'privkey' : ''}
      
    else:
      # User didn't upload pubkey, generate key pair for them
      key_dict = builder.generate_keypair()
    
    request.session[username] = key_dict
  
    print request.session.keys()
    print request.session.items()
    return HttpResponse("done")
  


def create_installer(request):
  """
  <Purpose>
    Sets up necessary variables needed for build_installer,
    specifically the key dictionary. The key dictionary is a
    dict whose keys are usernames, and whose values are key
    dicts (pubkey & privkey). See build_installer for more info. 
    
    Also generates a unique installer ID (not related to the django
    session ID). The installer ID is tied to this specific installer,
    and is used for public distribution (eg: person wants to give his
    friends a link to d/l his installers). 
    
    Then, of course, the installers are actually built and deposited
    into a folder related to the installer ID.
  
  <Notes>
    The vessel_dict being passed to this function via AJAX is a list
    of vessel dictionaries. Here is an example of the format:
    [ {owner, percentage, [users]}, {owner, percentage, [users]} ... ]
  """
  if not request.method == 'POST':
    return HttpResponseRedirect(reverse("installer_creator"))
  
  if (request.POST['action'] == 'createinstaller'):
    vessel_dict = simplejson.loads(request.POST['content'])
    print "VESSEL_DICT: "
    print vessel_dict
    
    # sanity check, and construct list of users included in the vessel_dict
    users_list = []
    for vessel in vessel_dict:
      if vessel['owner'] not in users_list:
        users_list.append(vessel['owner'])
      
      for user in vessel['users']:
        # check for duplicate users within ONE vessel
        if user != '' and vessel['users'].count(user) > 1:
          #print "DUPLICATE FOUND"
          return HttpResponse("ERROR: Duplicate users in same vessel!", status=500)
        if user not in users_list:
          users_list.append(user)
      
    # construct key dictionary of active users out of session key dict
    key_dict = {}
    for user in users_list:
      key_dict[user] = request.session[user]
    
    # generate installer ID
    installer_id = _generate_installer_id()
    print "INSTALLER_ID: " + installer_id
    
    # Begins the actual build of the installer
    installers_url_dict= {'w':'w', 'l':'l', 'm':'m'}
    
    try:
      #installers_url_dict = builder.build_installer(vessel_dict, key_dict, installer_id)
      pass
    except Exception, e:
      print str(e)
      return HttpResponse("<b>Build failed! We encountered a problem while building the installers.</b><br>" +
                          "Please contact us! Details:<br><br>" + str(e), status=500)
    
    # store these urls for the download page
    request.session['win_installer_url'] = installers_url_dict['w']
    request.session['linux_installer_url'] = installers_url_dict['l']
    request.session['mac_installer_url'] = installers_url_dict['m']
    
    return HttpResponse("Done")


def download_keys(request):
  return HttpResponse("Download keys...")
  

def download_installers(request):
  """
  <Purpose>
    Displays a page allowing users to download the created installers.
  """
  
  return direct_to_template(request, "download.html", 
                            {'win_installer_url' : request.session['win_installer_url'],
                             'linux_installer_url' : request.session['linux_installer_url'],
                             'mac_installer_url' : request.session['mac_installer_url']})


def _standarize(username):
  """
  <Purpose>
    Standarize the username by removing trailing whitespace, turning all
    letters to lower case, and replacing inner whitespace with underscores.
  """
  username = username.strip()
  username = username.lower()
  username = username.replace(" ", "_")
  
  return username


def _generate_installer_id():
  #TODO: Check whether md5ing the time is unique enough
  m = hashlib.md5()
  m.update(str(time.time()))
  return m.hexdigest()