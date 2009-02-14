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
from django.contrib.auth.models import User as DjangoUser

#session_start();
prefix = "/var/www/customized_installer"
carter_script = "/home/ivan/trunk/dist/customize_installers.py"
vesselinfopy = "/home/ivan/trunk/test/writecustominstallerinfo.py"
#sid = session_id()
dl_prefix = prefix + "/download/" + sid

def customized_installer(request):
    return direct_to_template(request,'customized_installer/index.html', {'username' : username})

def build_installer(request):
    if not isset(_POST):
        # redirect to err page
        pass
        
    if (_POST['action'] == 'adduser'):
        username = standarize(_POST['username'])
        if (is_uploaded_file(_FILES["publickey"]["tmp_name"])):
            key = file_get_contents(_FILES["publickey"]["tmp_name"])
            _SESSION[username] = key
        else:
            unset(_SESSION[username])
    elif (_POST['action'] == 'createinstaller'):
        vessels = json_decode(stripslashes(_POST['content']), true)
        os.system("rm $dl_prefix/*")
        os.system("mkdir $dl_prefix")
        os.system("mkdir $dl_prefix/vesselsinfo")
        //file_put_contents("h0","")
        for vessel in vessels:
            genkey(vessel['owner'])
            vessel['owner'] = getPublicKeyPath(standarize(vessel['owner']))
            for user in vessel['users']:
                genkey(user)
                user = getPublicKeyPath(standarize(user))

        file_put_contents("h1","")
        file_put_contents("$dl_prefix/vesselsinfo.txt", outputVesselsInfo($vessels))
        file_put_contents("h2","")
        os.system("python $vesselinfopy $dl_prefix/vesselsinfo.txt $dl_prefix/vesselsinfo/")
        
        # file_put_contents("h3","cd $dl_prefix/ && python $carter_script mlw $dl_prefix/vesselsinfo $dl_prefix/ > /tmp/carter.out.php 2> /tmp/carter.err.php")
        os.system("mkdir $dl_prefix/tmp/")
        os.system("cd $dl_prefix/ && python $carter_script mlw $dl_prefix/vesselsinfo $dl_prefix/ > /tmp/carter.out.php 2> /tmp/carter.err.php")
		
        # file_put_contents("h4","")
        os.system("zip -j $dl_prefix/private.zip $dl_prefix/*.privatekey")
        # file_put_contents("h5","")
        os.system("zip -j $dl_prefix/public.zip $dl_prefix/*.publickey")
        # file_put_contents("h6","")

def genkey(user):
    global prefix
    global dl_prefix
    if (array_key_exists(user, _SESSION)):
        file_put_contents(getPublicKeyPath(user), _SESSION[user])
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
