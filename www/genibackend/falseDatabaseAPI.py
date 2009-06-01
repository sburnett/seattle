# This is a test module for the database API
import random
from repyportability import *

databasedict = {'vesselmap':{}}
databaselock = getlock()

def init_database():
  pass

def write_vesselname_to_vesselmap(vesselname, username, expiretime=60*60*4):
  databaselock.acquire()
  try:
    if random.random()>.8:
      raise Exception("Random error adding entry")
  
    if 'vesselmap' not in databasedict:
      databasedict['vesselmap'] = {}
    if vesselname in databasedict['vesselmap']:
      print "Entry already exists in vesselmap!?!"
    else:
      databasedict['vesselmap'][vesselname] = username

  finally:
    databaselock.release()
  


def remove_vesselname_from_vesselmap(vesselname):
  databaselock.acquire()
  try:
    if random.random()>.8:
      raise Exception("Random error removing entry")
  
    if ('vesselmap' not in databasedict) or (vesselname not in databasedict['vesselmap']):
      print "Entry is not in vesselmap!?!"
    else:
      del databasedict['vesselmap'][vesselname]
  
  finally:
    databaselock.release()
  



def vesselname_is_in_vesselmap(vesselname):
  databaselock.acquire()
  try:
    if random.random()>.8:
      raise Exception("Random error checking entry")
  
    if 'vesselmap' not in databasedict:
      return False
    else:
      return vesselname in databasedict['vesselmap']
  
  finally:
    databaselock.release()
  

def get_ownerkeys_given_vesselname(vesselname):
  # return nonsensical keys...
  return ('1 2', '3 4')


def convert_vesselname_to_ipportid(vesselname):
  # return nonsensical information
  return ('127.0.0.1',11111,'v1')

