"""
<Program Name>
  models.py

<Started>
  October, 2008

<Author>
  ivan@cs.washington.edu
  Ivan Beschastnikh

<Purpose>
  Defines django model classes which are interfaces between django
  applications and the database

  This file contains definitions of model classes which are used by
  django to (1) create the django (geni) database schema, (2) to
  define an interface between django applications and the database and
  are used to maintain an evolvable schema that is easy to read,
  modify, and operate on.

  See http://docs.djangoproject.com/en/dev/topics/db/models/

<ToDo>
  This file needs to be cleaned up by moving all functions that
  operate on models out of this file and into a 'modelslib' file or
  the like. This file _should_ contain only model class definitions.
"""

import random
import datetime
import time

from geni.control.db_operations import pop_key
from django.db import models
from django.contrib.auth.models import User as DjangoUser


class User(models.Model):
    """
    <Purpose>
      Defines the geni user model
    <Side Effects>
      Provides an interface to the database
    <Example Use>
      See http://docs.djangoproject.com/en/dev/topics/db/models/
    """

    # link GENI user to django user record which authenticates users
    # on the website
    www_user = models.ForeignKey(DjangoUser,unique = True)
    # user's port
    port = models.IntegerField("User (vessel) port")
    # affiliation
    affiliation = models.CharField("Affiliation", max_length=1024)
    # user's personal public key
    pubkey = models.CharField("User public key", max_length=2048)
    # user's personal private key: only stored if generate during
    # registration, and (we recommend that the user delete these, once
    # they download them)
    privkey = models.CharField("User private key [!]", max_length=4096)
    # donor pub key
    donor_pubkey = models.CharField("Donor public key", max_length=2048)
    # donor priv key (user never sees this key
    donor_privkey = models.CharField("Donor private Key", max_length=4096)
    # number of vessels this user has acquired
    num_acquired_vessels = models.IntegerField("Number of acquired vessels")

    @classmethod
    def get_guser_by_username(cls, www_username):
        djusers = DjangoUser.objects.filter(username = www_username)
        if djusers.count() != 1:
            return False, None
        users = User.objects.filter(www_user = djusers[0])
        if djusers.count() != 1:
            return False, None
        return True, users[0]
    
    def __unicode__(self):
        """
        <Purpose>
          Produce a string representation of the User model class
        <Arguments>
          None
        <Exceptions>
          None
        <Side Effects>
          None
        <Returns>
          String representation of the User class
        """
        return self.www_user.username

    def save_new_user(self):
        """
        <Purpose>
          Handles the generation of keys and ports for a new user
          record, and then saves the new user record to the geni db.
        <Arguments>
          None
        <Exceptions>
          None
        <Side Effects>
          Saves a new User record to the geni db
        <Returns>
          True on success, or False on failure
        """
        # user ports permitted on vessels on a donated host
        ALLOWED_USER_PORTS = range(63100,63180)

        # generate user pub/priv key pair for accessing vessels
        if self.pubkey == "":
            pubpriv=pop_key()
            if pubpriv == []:
                return False
            self.pubkey,self.privkey = pubpriv
        # generate user pub/priv key pair for donation trackback
        pubpriv2=pop_key()
        if pubpriv2 == []:
            return False
        self.donor_pubkey,self.donor_privkey = pubpriv2
        # generate random port for user
        self.port = random.sample(ALLOWED_USER_PORTS, 1)[0]
        # set default num acquired vessels to 0
        self.num_acquired_vessels = 0
        self.save()
        return True

    def gen_new_key(self):
        """
        <Purpose>
          Generates and sets a new pub\priv key pair for the user
        <Arguments>
          None
        <Exceptions>
          None
        <Side Effects>
          Modifies and saves the User record to have a new pub\priv key pair
        <Returns>
          True on success, False on failure
        """
        pubpriv=pop_key()
        if pubpriv == []:
            return False
        self.pubkey,self.privkey = pubpriv
        self.save()
        return True

    def vessel_credit_remaining(self):
        """
        <Purpose>
          Returns the number of vessels this user is allowed
          to acquire at the moment.
        <Arguments>
          None
        <Exceptions>
          None
        <Side Effects>
          None
        <Returns>
          The number of vessels this user may acquire >= 0.
        """
        remaining = self.vessel_credit_limit() - self.num_acquired_vessels
        if remaining < 0:
            # this may happen when the vessels are in expiration mode
            # but aren't expired yet
            return 0
        return remaining

    def vessel_credit_limit(self):
        """
        <Purpose>
          Returns the maximum number of allowed vessels this user may acquire
        <Arguments>
          None
        <Exceptions>
          None
        <Side Effects>
          None
        <Returns>
          The number of vessels this user is allowed to acquire
        """
        num_donations = Donation.objects.filter(user=self).filter(active=1).count()
        max_num = 10 * (num_donations + 1)
        return max_num
    
class Donation(models.Model):
    """
    <Purpose>
      Defines the donation model
    <Side Effects>
      Provides an interface to the database
    <Example Use>
      See http://docs.djangoproject.com/en/dev/topics/db/models/
    """

    # user donating
    user = models.ForeignKey(User)
    # machine identifier
    pubkey = models.CharField("Host public key", max_length=1024)
    # machine ip (last IP known)
    ip = models.IPAddressField("Host IP address")
    # node manager port (last port known)
    port = models.IntegerField("Host node manager's port")
    # machine's subnet address (deduced from the last known IP)
    subnet = models.PositiveIntegerField("Host subnet address")
    # date this donation was added to the db, auto added to new instances saved
    date_added = models.DateTimeField("Date host added", auto_now_add=True)
    # date we last heard from this machine, this field will be updated
    # ** every time the object is saved **
    last_heard = models.DateTimeField("Last time machine responded", auto_now=True)
    # status: "Initializing", etc
    status = models.CharField("Node status", max_length=1024)
    # node's seattle version
    version = models.CharField("Node Version", max_length=64)
    # owner's public key
    # TODO: change to owner_pubkeystr
    owner_pubkey = models.CharField("Owner user public key", max_length=2048)
    # owner's private key
    # TODO: change to owner_privkeystr
    owner_privkey = models.CharField("Owner user private key", max_length=4096)
    # epoch indicates the last time that the onepercenttoonepercent
    # script contacted this node
    epoch = models.IntegerField("Epoch")
    # active indicates whether this donation counts or not -- when a
    # donation's epoch is older then some threshold from current
    # epoch, a donation is marked as inactive
    active = models.BooleanField()
    def __unicode__(self):
        """
        <Purpose>
          Produce a string representation of the Donation model class
        <Arguments>
          None
        <Exceptions>
          None
        <Side Effects>
          None
        <Returns>
          String representation of the Donation class
        """
        return "%s:%s:%d"%(self.user.www_user.username, self.ip, self.port)
        
class Vessel(models.Model):
    """
    <Purpose>
      Defines the vessel model
    <Side Effects>
      Provides an interface to the database
    <Example Use>
      See http://docs.djangoproject.com/en/dev/topics/db/models/
    """

    # corresponding donation
    donation = models.ForeignKey(Donation)
    # vessel's name, e.g. v1..v10
    name = models.CharField("Vessel name", max_length=8)
    # vessle's last status
    status = models.CharField("Vessel status", max_length=1024)
    # extravessel boolean -- if True, this vessel is used for advertisements of geni's key
    extra_vessel = models.BooleanField()
    # assigned -- if True this vessel is assigned to a user (i.e. there exists a VesselMap entry for this vessel)
    assigned = models.BooleanField()
    def __unicode__(self):
        """
        <Purpose>
          Produce a string representation of the Vessel model class
        <Arguments>
          None
        <Exceptions>
          None
        <Side Effects>
          None
        <Returns>
          String representation of the Vessel class
        """
        return "%s:%s"%(self.donation.ip,self.name)

class VesselPort(models.Model):
    """
    <Purpose>
      Defines the vesselport model
    <Side Effects>
      Provides an interface to the database
    <Example Use>
      See http://docs.djangoproject.com/en/dev/topics/db/models/
    """

    # corresponding vessel
    vessel = models.ForeignKey(Vessel)
    # vessel's port on this host
    port = models.IntegerField("Vessel port")
    def __unicode__(self):
        """
        <Purpose>
          Produce a string representation of the VesselPort model class
        <Arguments>
          None
        <Exceptions>
          None
        <Side Effects>
          None
        <Returns>
          String representation of the VesselPort class
        """
        return "%s:%s:%s"%(self.vessel.donation.ip, self.vessel.name, self.port)

class VesselMap(models.Model):
    """
    <Purpose>
      Defines the vesselmap model
    <Side Effects>
      Provides an interface to the database
    <Example Use>
      See http://docs.djangoproject.com/en/dev/topics/db/models/
    """

    # the vessel_port being assigned to a user
    vessel_port = models.ForeignKey(VesselPort)
    # the user assigned to the vessel
    user = models.ForeignKey(User)
    # expiration date/time
    expiration = models.DateTimeField("Mapping expiration date")
    def __unicode__(self):
        """
        <Purpose>
          Produce a string representation of the VesselMap model class
        <Arguments>
          None
        <Exceptions>
          None
        <Side Effects>
          None
        <Returns>
          String representation of the VesselMap class
        """
        return "%s:%s:%s"%(self.vessel_port.vessel.donation.ip, self.vessel_port.vessel.name, self.user.www_user.username)

    def time_remaining(self):
        """                                                                                                                                                                                                                                                                                                                
        <Purpose>                                                                                                                                                                                                                                                                                                          
          Returns the amount of time remaining to the assignment of                                                                                                                                                                                                                                                        
          a user to a vessel as a string                                                                                                                                                                                                                                                                                   
        <Arguments>                                                                                                                                                                                                                                                                                                        
          None                                                                                                                                                                                                                                                                                                             
        <Exceptions>                                                                                                                                                                                                                                                                                                       
          None                                                                                                                                                                                                                                                                                                             
        <Side Effects>                                                                                                                                                                                                                                                                                                     
          None                                                                                                                                                                                                                                                                                                             
        <Returns>                                                                                                                                                                                                                                                                                                          
          Number of seconds before the vessel expires                                                                                                                                                                                                                                                                      
        """
        curr_time = datetime.datetime.now()
        if self.expiration < curr_time:
            # expiration in the past                                                                                                                                                                                                                                                                                       
            ret = "now"
        else:
            delta = self.expiration - curr_time
            hours = delta.seconds / (60 * 60)
            minutes = (delta.seconds - (hours * 60 * 60)) / 60
            ret = str(hours) + "h " + str(minutes) + "m"
        return ret
    
class Share(models.Model):
    """
    <Purpose>
      Defines the share model
    <Side Effects>
      Provides an interface to the database
    <Example Use>
      See http://docs.djangoproject.com/en/dev/topics/db/models/
    """

    # user giving
    from_user = models.ForeignKey(User, related_name='from_user')
    # user receiving
    to_user = models.ForeignKey(User, related_name = 'to_user')
    # percent giving user is sharing with receiving user
    percent = models.DecimalField("Percent shared", max_digits=3, decimal_places=0)
    def __unicode__(self):
        """
        <Purpose>
          Produce a string representation of the Share model class
        <Arguments>
          None
        <Exceptions>
          None
        <Side Effects>
          None
        <Returns>
          String representation of the Share class
        """
        return "%s->%s"%(self.from_user.www_user.username,self.to_user.www_user.username)
