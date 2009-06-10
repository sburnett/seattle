"""
<Program Name>
  customized_installer/views.py

<Started>
  February, 2008

<Author>
  ivan@cs.washington.edu
  Ivan Beschastnikh
  
  shawiz@cs.washington.edu
  Sean (Xuanhua) Ren

<Purpose>
  Defines view functions that handle HTTP requests

  This file contains view functions for the web installers application which
  are called whenever a url is matched in geni.urls. These
  functions always take an HTTP request object, and return an HTTP
  response object, which is sometimes generated automatically by
  referencing a template via direct_to_template() and other
  django shorthands.

  For more information on views in django see:
  See http://docs.djangoproject.com/en/dev/topics/http/views/
"""

import string
import os

from django.views.generic.simple import direct_to_template, redirect_to
from django.http import HttpResponse
from django import forms
from django.contrib.auth.models import User as DjangoUser
from django.utils import simplejson
import xmlrpclib


user_key_dict = {}

def customized_installer(request):
  """
  <Purpose>
    Provides the main view for the customized installer application. 

  <Arguments>
    request:
      HTTP Request object

  <Exceptions>
    None?

  <Side Effects>
    None

  <Returns>
    On success returns an HTTP response that shows the main page for customized
    installer
    On failure, displays whatever the HTTP response for the failure, as returned
    by __get__guser__
  """
  return direct_to_template(request,'customized_installer/index.html', {})


def help(request):
  """
  <Purpose>
    Provides a 'help' view for the customized installer application. 

  <Arguments>
    request:
      HTTP Request object

  <Exceptions>
    None?

  <Side Effects>
    None

  <Returns>
    On success returns an HTTP response that shows the help page
    On failure, displays whatever the HTTP response for the failure, as
    returned by __get__guser__
  """
  return direct_to_template(request,'customized_installer/help.html', {})


def reset_form(request):
  """
	<Purpose>
		Add the given username and calculated key to the global user_key_dict
		If a text file had been uploaded, save it as the key; otherwise, use
		genkey function to generate a key for it. 
	<Arguments>
		request:
			HTTP Request Object that encapsulates the username and possibly a text file
			that has the key to the user
	<Side Effect>		
		Add username and key pair to the global user_key_dict
	<Returns>
	  A HttpResponse that confirms the operation
	<TODOs>
	  Make this function robust
	  make use of session, keeping the information in the download page
	  Ideally, it should return a warning if the action fails and the username when successes
	"""
  global user_key_dict
  if (request.POST['action'] == 'reset_form'):
    username = standarize(request.POST['username'])
    if 'publickey' in request.FILES:
      file = request.FILES['publickey']
      if file.size > 2048:
        return HttpResponse("Public key too large, file size limit is 2048 bytes")
      key = file.read()
    else:
      key = genkey(username)
    user_key_dict[username] = genkey(username)
    request.session[username] = key
      
    return HttpResponse("Done")
    

def build_installer(request):
  """
	<Purpose>
		Build the installer on remote server from json query passed in
	<Arguments>
		request:
			HTTP Request Object that encapsulates the user infomation in json 
	<Side Effect>		
		None
	<Returns>
	  dictionary of urls returned by the remote server
	<TODOs>
	  Make sure that the server returns the url
	  Save the url in session
	"""
  server = xmlrpclib.Server('http://localhost:8081')
  global user_key_dict
  if (request.POST['action'] == 'build_installer'):
    vessel_info = simplejson.loads(request.POST['content'])
    return server.build_installer(user_key_dict, vessel_info, 'wlm')


def genkey(username):
	"""
	<Purpose>
		Internal method to generate keys for users
	<Arguments>
		username:
			the user who we want to generate key for
	<Side Effect>		
    None
	<Returns>
		the key for the user
	<TODOs>
	  complete this function
	"""

	# write keys to the file
	#os.system("python generatekeys.py %s %s %s"%(username, 20, "keys"))

	# read the public key from file
	#f = open("/keys/%s.public"%(username), 'r')
	#key = f.read()
	#f.close()
	key = '12312312'
	return key


def standarize(username):
  """
	<Purpose>
	  Standarize the username format by removing trailing whitespace
	  turn all letters to lower case, and replace inner whitespace with _
	<Arguments>
		The username string needs to be standarized 
	<Side Effect>		
		None
	<Returns>
	  The standarized username
	"""
  # remove trailing whitespace
  username = username.strip()
  # lowercase
  username = username.lower()
  # replace all inner whitespace chars with _
  username = string.join(string.split(username),'_')
  return username


def download(request):
  """
  <Purpose>
    Provides a 'download' view for the download application. 

  <Arguments>
    request:
      HTTP Request object
    username (string):
      A string representing the GENI user's username into the GENI portal
      
  <Exceptions>
    None?

  <Side Effects>
    None

  <Returns>
    On success returns an HTTP response that show the download page
    of the installers that are donating resources to user with
    username 'username'. On failure, displays whatever the HTTP
    response for the failure, as returned by __get__guser__
    
  <TODOs>
    Work on the download page so that it takes the url of installer from session
    and include these urls on the page
  """
  
  return direct_to_template(request,'customized_installer/download.html')