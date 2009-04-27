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
import 


#session_start();
#sid = session_id()

def customized_installer(request):
    return direct_to_template(request,'customized_installer/index.html', {})

def help(request):
    return direct_to_template(request,'customized_installer/help.html', {})

def build_installer(request):
    if (request.POST['action'] == 'adduser'):
        username = standarize(request.POST['username'])
        if (request.FILES['file']['content']):
            key = FILES['file']['content'])
            request.session[username] = key
        else:
            del request.session[username]
    elif (request.POST['action'] == 'createinstaller'):
        
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
