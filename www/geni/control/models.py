import random
from django.db import models
from django.contrib.auth.models import User as DjangoUser
from django.db import connection
from django.db import transaction
from geni.changeusers import changeusers
import datetime
import time
import traceback

# user ports permitted on vessels on a donated host
allowed_user_ports = range(63100,63180)
# 7 days worth of seconds
VESSEL_EXPIRE_TIME_SECS = 604800

def pop_key():
    cursor = connection.cursor()
    cursor.execute("BEGIN")
    cursor.execute("SELECT id,pub,priv FROM keygen.keys_512 limit 1")
    row = cursor.fetchone()
    if row == ():
        cursor.execute("ABORT")
        return []
    cursor.execute("DELETE from keygen.keys_512 WHERE id=%d"%(row[0]))
    cursor.execute("COMMIT")
    return [row[1],row[2]]

def get_unacquired_vessels():
    vmaps = VesselMap.objects.all()
    vexclude = []
    for vmap in vmaps:
        vexclude.append(vmap.vessel)

    vret = []
    for v in Vessel.objects.all():
        if v not in vexclude:
            vret.append(v)
    return vret

@transaction.commit_manually    
def acquire_resources(geni_user, num, type):
    '''
    attempts to acquire num vessels for geni_user of some network type (LAN,WAN,RAND)
    '''
    expire_time = datetime.datetime.fromtimestamp(time.time() + VESSEL_EXPIRE_TIME_SECS)
    explanation = ""
    try:
        # FIXME: we ignore type of vessel requested (for now)
        #vessel = Vessel.objects.exclude(vesselmap__vessel__exact
        vessels = get_unacquired_vessels()
    
        if num > len(vessels):
            num = len(vessels)
            explanation += "No more vessels available (max %d)."%(num)
        else:
            explanation += "Attempting to acquire %d vessels out of %d available."%(num,len(vessels))
            
        acquired = 0
        for v in vessels:
            if (acquired >= num):
                break

            # issue the command to remote nodemanager
            userpubkeystringlist = [geni_user.pubkey]
            nmip = v.donation.ip
            nmport = v.donation.port
            vesselname = v.name
            nodepubkey = v.donation.owner_pubkey
            nodeprivkey = v.donation.owner_privkey
            explanation += " %s:%s:%s - \n\n"%(nmip,nmport,vesselname)
            # explanation += "nodepubkey : %s<br>nodeprivkey: %s<br>"%(nodepubkey,nodeprivkey)
            success,msg = changeusers(userpubkeystringlist, nmip, nmport, vesselname, nodepubkey, nodeprivkey)
            if success:
                acquired += 1
                # create and save the new vmap entry
                vmap = VesselMap(vessel = v, user = geni_user, expiration = "%s"%(expire_time))
                vmap.save()
                explanation += " added, "
            else:
                explanation += "%s, "%(msg)
            
        if (num - acquired) != 0:
            explanation += "Failed to acquire %d nodes."%(num-acquired)
            
    except:
        # a hack to get the traceback information into a string by
        # printing to file and then reading back from file
        f = open("/tmp/models_trace","w")
        traceback.print_exc(None,f)
        f.close()
        f = open("/tmp/models_trace","r")
        explanation += f.read()
        f.close()
        transaction.rollback()
        return False, explanation
    else:
        transaction.commit()
        explanation += "Acquired %d nodes. "%(num) + explanation
        return True,num,explanation

class User(models.Model):
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
    
    def __unicode__(self):
        return self.www_user.username

    def save_new_user(self):
        global allowed_user_ports

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
        self.port = random.sample(allowed_user_ports, 1)[0]
        self.save()
        return True

    def gen_new_key(self):
        pubpriv=pop_key()
        if pubpriv == []:
            return False
        self.pubkey,self.privkey = pubpriv
        self.save()
        return True
    
class Donation(models.Model):
    # user donating
    user = models.ForeignKey(User)
    # machine identifier
    pubkey = models.CharField("Host public key", max_length=1024)
    # machine ip (last IP known)
    ip = models.IPAddressField("Host IP address")
    # node manager port (last port known)
    port = models.IntegerField("Host node manager's port")
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
    owner_pubkey = models.CharField("Owner user public key", max_length=2048)
    # owner's private key
    owner_privkey = models.CharField("Owner user private key", max_length=4096)
    
    def __unicode__(self):
        return "%s:%s:%d"%(self.user.www_user.username, self.ip, self.port)
        
class Vessel(models.Model):
    # corresponding donation
    donation = models.ForeignKey(Donation)
    # vessel's name, e.g. v1..v10
    name = models.CharField("Vessel name", max_length=8)
    # vessle's last status
    status = models.CharField("Vessel status", max_length=1024)
    # extravessel boolean -- if True, this vessel is used for advertisements of geni's key
    extra_vessel = models.BooleanField()
    def __unicode__(self):
        return "%s:%s"%(self.donation.ip,self.name)

class VesselPorts(models.Model):
    # corresponding vessel
    vessel = models.ForeignKey(Vessel)
    # vessel's port on this host
    port = models.IntegerField("Vessel port")
    def __unicode__(self):
        return "%s:%s:%s"%(self.vessel.donation.ip, self.vessel.name, self.port)

class VesselMap(models.Model):
    # the vessel being assigned to a user
    vessel = models.ForeignKey(Vessel)
    # the user assigned to the vessel
    user = models.ForeignKey(User)
    # expiration date/time
    expiration = models.DateTimeField("Mapping expiration date")
    def __unicode__(self):
        return "%s:%s:%s"%(self.vessel.donation.ip, self.vessel.name, self.user.www_user.username)

    
class Share(models.Model):
    # user giving
    from_user = models.ForeignKey(User, related_name='from_user')
    # user receiving
    to_user = models.ForeignKey(User, related_name = 'to_user')
    # percent giving user is sharing with receiving user
    percent = models.DecimalField("Percent shared", max_digits=3, decimal_places=0)
    def __unicode__(self):
        return "%s->%s"%(self.from_user.www_user.username,self.to_user.www_user.username)
