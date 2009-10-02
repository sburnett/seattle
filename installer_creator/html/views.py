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
import os
import StringIO
import tempfile
import time
import zipfile
import random

from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.views.generic.simple import direct_to_template
from django.utils import simplejson

from installer_creator import settings
from installer_creator.common import builder
from installer_creator.common import validations 

INSTALLER_ID_LENGTH = 32


def installer_creator(request):
  """
  <Purpose>
    Displays the main installer creator page.
    Flushes the session, so users start off with a clean dict.
  """
  
  # Flush the session dict, so new & returning users get a clean dict
  request.session.flush()
  
  return direct_to_template(request, 'mainpage.html', {})
  

def check_session(request):
  """
  <Purpose>
    Called via AJAX, and simply returns whether or not the session dict is
    clean or dirty. If clean (session dict has no entries), the JS on the 
    main page does nothing. If the session dict is dirty (contains key entries),
    then the JS on the page will refresh the page, triggering a session flush 
    from the installer_creator() view function.
  """
  if not request.method == 'POST' or request.POST['action'] != 'checksession':
    return HttpResponseRedirect(reverse("installer_creator"))

  if request.session.items():
    return HttpResponse("need_refresh")
  else:
    return HttpResponse("no_refresh")
    

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
    request.session['installer_id'] = installer_id
    
    # Begins the actual build of the installer
    try:
      #builder.build_installer(vessel_dict, key_dict, installer_id)
      pass
    except Exception, e:
      print str(e)
      return HttpResponse("<b>Build failed! We encountered a problem while building the installers.</b><br>" +
                          "Please contact us! Details:<br><br>" + str(e), status=500)
    
    # store these urls for the download page
#    request.session['win_installer_url'] = installers_url_dict['w']
#    request.session['linux_installer_url'] = installers_url_dict['l']
#    request.session['mac_installer_url'] = installers_url_dict['m']
    
    # store keydict for download keys page
    request.session['key_dict'] = key_dict
    
    return HttpResponse("Done")



def download_keys(request):
  """
  <Purpose>
    Displays a page allowing users to download their keys.
  """
  return direct_to_template(request, "downloadkeys.html", 
                            {'installer_id' : request.session['installer_id']})



def dl_keys(request):
  """
  <Purpose>
    Returns the user's keys as a downloadable object (zip file w/ keys)
  """
  key_dict = request.session['key_dict']
  
  # init file object that will hold zipfile in memory
  #fhandle_zip = StringIO.StringIO
  gen = _generate_random()
  print gen
  fhandle_zip_path = os.path.join(tempfile.gettempdir(), gen)
  fhandle_zip = open(fhandle_zip_path, 'wb')
  
  # init zipfile object
  zipper = zipfile.ZipFile(fhandle_zip, 'w')
  
  for user in key_dict:
    username = str(user)
    pubkey = key_dict[user]['pubkey']
    privkey = key_dict[user]['privkey']
    
    # write out pubkey
    pubkey_path = _write_to_temp_file(pubkey)
    zipper.write(pubkey_path, username + '.publickey')
    # remove temporary pubkey file
    os.remove(pubkey_path)
    
    if privkey != '':
      # write out privkey
      privkey_path = _write_to_temp_file(privkey)
      zipper.write(privkey_path, username + '.privatekey')
      # remove temporary privkey file
      os.remove(privkey_path)
  
  public_url = "Give this link to others so they can donate on your behalf:\n"
  public_url += "https://" + request.get_host() + reverse("download_installers", args=[request.session['installer_id']])
  public_url_path = _write_to_temp_file(public_url) 
  zipper.write(public_url_path, "public_installer_url.txt")
  # remove temporary pub url file
  os.remove(public_url_path)
  
  zipper.close()
  fhandle_zip.close()
  
  fp = open(fhandle_zip_path, 'rb')
  response = HttpResponse(fp.read(), mimetype='application/x-zip-compressed')
  response['Content-Disposition'] = 'attachment; filename=SeattleInstaller_Info.zip'
  fp.close()

  # clean up temporary zip file
  os.remove(fhandle_zip_path)
  
  return response


#def post_install(request):
#  domain = "https://" + request.get_host()
#  installer_id = request.session['installer_id']
#  
#  return direct_to_template(request, "download.html", 
#                            {'win_installer_url' : settings.USER_INSTALLERS_URL + "%s_dist/seattle_win.zip"%(installer_id),
#                             'linux_installer_url' : settings.USER_INSTALLERS_URL + "%s_dist/seattle_linux.tgz"%(installer_id),
#                             'mac_installer_url' : settings.USER_INSTALLERS_URL + "%s_dist/seattle_mac.tgz"%(installer_id),
#                             'just_installed' : 'true',
#                             'domain' : domain,
#                             'installer_id' : installer_id})


def download_installers(request, installer_id):
  """
  <Purpose>
    Displays a page allowing users to download the created installers.
  """
  # check if installer instance EXISTS 
  
  result = builder.check_and_build_if_new_installers(installer_id)
  
  if result == -1:
    return HttpResponse("Error! Couldn't find base installers during check_and_build_if_new_installers().", status=500)
  
  domain = "https://" + request.get_host()
  
  return direct_to_template(request, "download.html", 
                            {'win_installer_url' : settings.USER_INSTALLERS_URL + "%s_dist/seattle_win.zip"%(installer_id),
                             'linux_installer_url' : settings.USER_INSTALLERS_URL + "%s_dist/seattle_linux.tgz"%(installer_id),
                             'mac_installer_url' : settings.USER_INSTALLERS_URL + "%s_dist/seattle_mac.tgz"%(installer_id),
                             'domain' : domain,
                             'installer_id' : installer_id})


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
  """
  <Purpose>
    Generates a random installer ID.
  """
  #TODO: Check whether md5ing the time is unique enough
  m = hashlib.md5()
  m.update(str(time.time()))
  return m.hexdigest()

def _generate_random():
  """
  <Purpose>
    Generates a random string.
  """
  population = []
  population.extend(range(ord('0'), ord('9') + 1))
  population.extend(range(ord('A'), ord('Z') + 1))
  
  key = ""
  for character in random.sample(population, 30):
    key += chr(character)
  
  return key

def _write_to_temp_file(data):
  """
  <Purpose>
    Writes the given string to a temporary file.
    NOTE: Doesn't remove the temporary file for you! You must take care of this yourself.
   
   <Returns>
     The path to the created temporary file. 
  """
  gen = _generate_random()
  
  fhandle_path = os.path.join(tempfile.gettempdir(), gen)
  fhandle = open(fhandle_path, 'w')
  fhandle.write(data)
  fhandle.close()
  
  return fhandle_path
