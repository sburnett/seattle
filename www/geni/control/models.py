from django.db import models
from django.contrib.auth.models import User as DjangoUser

class User(models.Model):
    # link GENI user to django user record which authenticates users
    # on the website
    www_user = models.ForeignKey(DjangoUser,unique = True)
    # user's port
    port = models.IntegerField("User's port")
    # affiliation
    affiliation = models.CharField("Affiliation", max_length=1024)
    def __unicode__(self):
        return self.www_user.username
    
class Donation(models.Model):
    # user donating
    user = models.ForeignKey(User)
    # machine identifier
    pubkey = models.CharField("Host public key", max_length=1024)
    # machine ip
    ip = models.IPAddressField("Host IP address")
    # node manager port
    port = models.IntegerField("Host node manager's port")
    # date this donation was added to the db
    date_added = models.DateTimeField("Date host added", auto_now_add=True)
    # date we last heard from this machine, this field will be updated
    # every time the object is saved
    last_heard = models.DateTimeField("Last time machine responded", auto_now=True)
    def __unicode__(self):
        return "%s:%s:%d"%(self.user.www_user.username, self.ip, self.port)
        
class Vessel(models.Model):
    # corresponding donation
    donation = models.ForeignKey(Donation)
    expiration = models.DateTimeField("Vessel expiration date")
    port = models.IntegerField("Vessel port")
    name = models.CharField("Vessel name", max_length=8)
    def __unicode__(self):
        return "%s:%s"%(self.donation.ip,self.name)

class VesselMap(models.Model):
    # the vessel being assigned to a user
    vessel = models.ForeignKey(Vessel)
    # the user assigned to the vessel
    user = models.ForeignKey(User)
    def __unicode__(self):
        return "%s:%s"%(self.vessel.name,self.user.www_user.username)
    
class Share(models.Model):
    # user giving
    from_user = models.ForeignKey(User, related_name='from_user')
    # user receiving
    to_user = models.ForeignKey(User, related_name = 'to_user')
    # percent giving user is sharing with receiving user
    percent = models.DecimalField("Percent shared", max_digits=3, decimal_places=0)
    def __unicode__(self):
        return "%s->%s"%(self.from_user.www_user.username,self.to_user.www_user.username)
