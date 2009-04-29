"""
<Program Name>
  customized_installer/views.py

<Started>
  February, 2008

<Author>
  ivan@cs.washington.edu
  Ivan Beschastnikh

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


def customized_installer(request):
  return direct_to_template(request,'customized_installer/index.html', {})


def help(request):
  return direct_to_template(request,'customized_installer/help.html', {})

  
def __jsonify(data):
  """
  <Purpose>
    Turns data into json representation (marshalls data), and
    generates and returns an HttpResponse object that will communicate
    the json representation of data to the client.

  <Arguments>
    data: data to marshall to the client as json. Typically this is a
    simple datatype, such as a dictionary, or an array, of strings/ints.

  <Exceptions>
    None?

  <Side Effects>
    None

  <Returns>
    An HTTP response object the has mimetype set to application/json
  """
  json = simplejson.dumps(data)
  return HttpResponse(json, mimetype='application/json')


def build_installer(request):
  if (request.POST['action'] == 'adduser'):
    username = standarize(request.POST['username'])
    if 'publickey' in request.FILES:
      file = request.FILES['publickey']
      if file.size > 2048:
        return HttpResponse("Public key too large, file size limit is 2048 bytes")
      key = file.read()
      request.session[username] = key
    else:
      del request.session[username]
    return True
  
  elif (request.POST['action'] == 'build_installer'):
    vessels = simplejson.loads(request.POST['content'])
    for vessel in vessels:
      genkey(vessel['owner'], request)
      vessel['owner'] = getPublicKeyPath(standarize(vessel['owner']))
      for user in vessel['users']:
        genkey(user, request)
        user = getPublicKeyPath(standarize(user))
    vessel_info = outputVesselsInfo(vessels)
    

def genkey(user, request):
  global prefix
  global dl_prefix
  if (array_key_exists(user, request.session)):
    file_put_contents(getPublicKeyPath(user), request.session[user])
  else:
    os.system("python $prefix/generatekeys.py $user 128 $dl_prefix/")


def outputVesselsInfo(vessels):
  output = ''
  for vessel in vessels:
    output += "Percent " + vessel['percentage'] + "\n"
    output += "Owner " + vessel['owner'] + "\n"
    for user in vessel['users']:
      output += "User " + user + "\n"
  return output


def standarize(username):
  # remove trailing whitespace
  username = username.strip()
  # lowercase
  username = username.lower()
  # replace all inner whitespace chars with _
  username = string.join(string.split(username),'_')
  return username


def getPublicKeyPath(username):
  global dl_prefix
  return dl_prefix + "/" + username + ".publickey"


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
  """
  
  return direct_to_template(request,'customized_installer/download.html')