""" 
Author: Justin Cappos

Start Date: Sept 1st, 2008

Description:
The advertisement functionality for the node manager

"""

import advertise

import misc

import threading

# The frequency of updating the advertisements
adfrequency = 300

# the TTL of those adverts
adTTL = 750

myname = None


class advertthread(threading.Thread):

  # Note: This will get updates from the main program because the dictionary
  # isn't a copy, but a reference to the same data structure
  addict = None


  def __init__(self,advertisementdictionary):
    self.addict = advertisementdictionary
    threading.Thread.__init__(self, name = "Advertisement Thread")

  def run(self):
    while True:
      # the list of controlling public keys
      advertkeys = []
      # make a copy so there isn't an issue with a race
      for vesselname in self.addict.keys()[:]:

        try:
          thisentry = self.addict[vesselname].copy()
        except KeyError:
          # the entry must have been removed in the meantime.   Skip it!
          continue

        # if I advertise the vessel...
        if thisentry['advertise']:
          # add the owner key if not there already...
          if thisentry['ownerkey'] not in advertkeys:
            advertkeys.append(thisentry['ownerkey'])

          # and all user keys if not there already
          for userkey in thisentry['userkeys']:
            if userkey not in advertkeys:
              advertkeys.append(userkey)

      # now that I know who to announce to, send messages to annouce my IP and 
      # port to all keys I support
      for key in advertkeys:
        try:
          advertise.announce(key, str(myname), adTTL)
        except Exception, e:
          print e
          # print the error and exit (we'll be restarted)
          return

      # wait to avoid sending too frequently
      misc.do_sleep(adfrequency)




