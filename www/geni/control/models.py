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
# 4 hours worth of seconds
VESSEL_EXPIRE_TIME_SECS = 14400


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

def get_unacquired_vessels(geni_user, filter_str):
    vmaps = VesselMap.objects.all()
    vexclude = []
    for vmap in vmaps:
        vexclude.append(vmap.vessel)

    vret = []
    for v in Vessel.objects.all():
        # filter out extra_vessels
        if v.extra_vessel:
            continue
        
        # perform filtering on ip (for LAN nodes)
        if filter_str != "" and filter_str not in v.donation.ip:
            continue
        # exclude vessels that are used
        if v in vexclude:
            continue
        # exclude vessels that don't have the port assigned to the user
        vports = VesselPorts.objects.filter(vessel = v)
        valid_port = False
        for vport in vports:
            if vport.port == geni_user.port:
                valid_port = True
        if not valid_port:
            continue
        
        vret.append(v)
    random.shuffle(vret)
    return vret

def release_resources(geni_user, resource_id, all):
    myresources = VesselMap.objects.filter(user=geni_user)

    for r in myresources:
        if (all is True) or (r.id == resource_id):
            nmip = r.vessel.donation.ip
            nmport = int(r.vessel.donation.port)
            vesselname = r.vessel.name
            nodepubkey = r.vessel.donation.owner_pubkey
            nodeprivkey = r.vessel.donation.owner_privkey
            success,msg = changeusers([""], nmip, nmport, vesselname, nodepubkey, nodeprivkey)
            if not success:
                print msg
            r.delete()
    return True
            
@transaction.commit_manually    
def acquire_resources(geni_user, num, type):
    '''
    attempts to acquire num vessels for geni_user of some network type (LAN,WAN,RAND)
    '''
    expire_time = datetime.datetime.fromtimestamp(time.time() + VESSEL_EXPIRE_TIME_SECS)
    explanation = ""
    try:
        # FIXME: we ignore type of vessel requested (for now)

        filter_ips = ""
        if int(type) == 1:
            # type is LAN
            filter_ips = "128.208.1."
        vessels_free = get_unacquired_vessels(geni_user, filter_ips)
        vessels = []
        if int(type) == 2:
            # type is WAN
            for v in vessels_free:
                if "128.208.1." not in v.donation.ip:
                    vessels.append(v)
                    
        summary = ""
        if num > len(vessels):
            num = len(vessels)
            explanation += "No more nodes available (max %d)."%(num)
            transaction.rollback()
            summary += " No nodes available to acquire."
            return False, explanation, summary
        else:
            explanation += "Attempted to acquire %d node(s) out of %d available."%(num,len(vessels))
            
        acquired = 0
        #num_failed = 0
        for v in vessels:
            if (acquired >= num):
                break

            # issue the command to remote nodemanager
            userpubkeystringlist = [geni_user.pubkey]
            nmip = v.donation.ip
            nmport = int(v.donation.port)
            vesselname = v.name
            nodepubkey = v.donation.owner_pubkey
            nodeprivkey = v.donation.owner_privkey
            # explanation += " %s:%s:%s - \n\n"%(nmip,nmport,vesselname)
            # explanation += "nodepubkey : %s<br>nodeprivkey: %s<br>"%(nodepubkey,nodeprivkey)
            # explanation += "calling changeusers with: \npubkeystrlist %s\nnmip %s\nnmport %s\nvesselname %s\nnodepubkey %s\nnodeprivkey %s\n"%(userpubkeystringlist, nmip, nmport, vesselname, nodepubkey, nodeprivkey)
            # explanation += " Acquiring %s:%s"%(nmip,nmport)
            success,msg = changeusers(userpubkeystringlist, nmip, nmport, vesselname, nodepubkey, nodeprivkey)
            if success:
                acquired += 1
                # create and save the new vmap entry
                vmap = VesselMap(vessel = v, user = geni_user, expiration = "%s"%(expire_time))
                vmap.save()
            else:
                explanation += " " + nmip + ":" + str(nmport) + " " + msg
            #else:
            #    explanation += msg
            #    break
                #explanation += " added, "
            #else:
            # explanation += "%s, "%(msg)
                #num_failed += 1
            
        if (num - acquired) != 0:
            summary += " Failed to acquire %d node(s)."%(num-acquired)
            
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
        summary += " Failed to acquire node(s). Internal Error."
        return False, explanation, summary
    else:
        transaction.commit()
        if acquired == 0:
            return False, explanation,summary
        summary += " Acquired %d node(s). "%(acquired)
        return True,acquired,explanation,summary

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

def test_acquire(username, num_nodes):
    user = DjangoUser.objects.get(username=username)
    print "django user: ", user
    geni_user = User.objects.get(www_user = user)
    print "geni user: ", geni_user
    ret = acquire_resources(geni_user, num_nodes, "LAN")
    print "acquire returned: ", ret
    if ret[0] == False:
        print ret[1]

def test_acquire_node(username,nodeip,vesselname):
    user = DjangoUser.objects.get(username=username)
    print "django user: ", user
    geni_user = User.objects.get(www_user = user)
    print "geni user: ", geni_user

    d = Donation.objects.get(ip = nodeip)
    print "donation: " , d
    v = Vessel.objects.get(donation = d, name = vesselname)
    print "vessel: ", v
    
    # issue the command to remote nodemanager
    userpubkeystringlist = [geni_user.pubkey]
    nmip = v.donation.ip
    nmport = int(v.donation.port)
    vesselname = v.name
    nodepubkey = v.donation.owner_pubkey
    nodeprivkey = v.donation.owner_privkey
    print "calling changeusers with: \npubkeystrlist %s\nnmip %s\nnmport %s\nvesselname %s\nnodepubkey %s\nnodeprivkey %s\n"%(userpubkeystringlist, nmip, nmport, vesselname, nodepubkey, nodeprivkey)
    success,msg = changeusers(userpubkeystringlist, nmip, nmport, vesselname, nodepubkey, nodeprivkey)
    print "returned: ", success, msg
