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
import sys
import traceback

from django.db import models
from django.contrib.auth.models import User as DjangoUser
from django.db import connection
from django.db import transaction
# from node_state_transitions.changeusers import changeusers

# 4 hours worth of seconds
VESSEL_EXPIRE_TIME_SECS = 14400

def pop_key():
    """
    <Purpose>
      Returns a new, never used 512 bit public and private key
    <Arguments>
      None
    <Exceptions>
      None
    <Side Effects>
      Deletes the returned key from the keygen.keys_512 table
    <Returns>
      [] if no more keys are available
      [public,private] new key pair
    """
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

def acquire_vessel(vessel, pubkey_list):
    """
    <Purpose>
      Responsible for changing the user public keys list on a vessel
    <Arguments>
      pubkey_list:
        list of public keys to associate as user keys with the vessel
      vessel:
        instance of Vessel class on which we need to set the user keys
    <Exceptions>
      None?
    <Side Effects>
      Changes the user public keys of a remote vessel
    <Returns>
      Returns True on success
      Returns (False, explanation) on failure where explanation is a
      string that explains the failure
    """
    # issue the command to remote nodemanager
    userpubkeystringlist = pubkey_list
    nmip = vessel.donation.ip
    nmport = int(vessel.donation.port)
    vesselname = vessel.name
    nodepubkey = vessel.donation.owner_pubkey
    nodeprivkey = vessel.donation.owner_privkey
    # explanation += " %s:%s:%s - \n\n"%(nmip,nmport,vesselname)
    # explanation += "nodepubkey : %s<br>nodeprivkey: %s<br>"%(nodepubkey,nodeprivkey)
    # explanation += "calling changeusers with: \npubkeystrlist %s\nnmip %s\nnmport %s\nvesselname %s\nnodepubkey %s\nnodeprivkey %s\n"%(userpubkeystringlist, nmip, nmport, vesselname, nodepubkey, nodeprivkey)
    # explanation += " Acquiring %s:%s"%(nmip,nmport)
    print "changeusers ", time.time()
    success,msg = changeusers(userpubkeystringlist, nmip, nmport, vesselname, nodepubkey, nodeprivkey)
    print "/changeusers " , time.time()

    if success:
        return True, ""
    explanation = nmip + ":" + str(nmport) + " " + msg
    return False, explanation


def get_base_vessels(geni_user):
    """
    <Purpose>

      Returns a base QuerySet of vessels that should accomodate a
      user. The QuerySet vessels are filtered based on:
      1) non-extra vessels only
      2) vessels supporting the user's port
      3) vessels are unassigned
      4) vessels are on active donations
    <Arguments>
      geni_user:
        an instance of the User class record for whom the vessels are intended
    <Exceptions>
      None?
    <Side Effects>
      None
    <Returns>
      Returns a django QuerySet object containing the vessel records
      matching the stated requirements
    """
    # consider vessels that are not 'extra vessels'
    v_non_extra = Vessel.objects.filter(extra_vessel=False)
    # consider vessels that match the geni_user's assigned port
    v_right_port = v_non_extra.filter(vesselport__port__exact=geni_user.port)
    # consider unassigned vessels
    v_unacquired = v_right_port.exclude(vesselport__vesselmap__isnull=False)
    # consider vessels on currently active donations
    v_active = v_unacquired.filter(donation__active__exact=True)
    print "v_non_extra", v_non_extra.count()
    print "v_right_port", v_right_port.count()
    print "v_unacquired", v_unacquired.count()
    print "v_active", v_active.count()
    return v_active

def create_vmaps(vessels, geni_user):
    """
    <Purpose>
      Creates the VesselMap class instances matching the vessels and
      saves them to the GENI database associated with the geni_user
    <Arguments>
      vessels:
        An array of vessels for which to create the VesselMap entries
      geni_user:
        An instance of class User to match on VesselMap instances
    <Exceptions>
      None
    <Side Effects>
      Creates new vesselmap database entries
    <Returns>
      True on success, False on failure
    """
    expire_time = datetime.datetime.fromtimestamp(time.time() + VESSEL_EXPIRE_TIME_SECS)
    for v in vessels:
        # find the vessel port entry corresponding to this vessel and user's port
        vports = VesselPort.objects.filter(vessel = v).filter(port = geni_user.port)
        if len(vports) != 1:
            return False
        vport = vports[0]
        # create and save the new vmap entries
        print "create and save vmap ", time.time()
        vmap = VesselMap(vessel_port = vport, user = geni_user, expiration = str(expire_time))
        vmap.save()
        print "/create and save vmap ", time.time()
    return True


def release_vessels(vessels):
    """
    <Purpose>
      'Releases' a list of vessels by performing a changeusers on each
      vessel and setting the user pubkeys list to [] on each vessel.
    <Arguments>
      vessels:
        a list of vessels to release
    <Exceptions>
      None -- exceptions triggered by change users are caught and
      ignored. The idea is to release as many vessels as possible.
    <Side Effects>
      Changes the user keys on vessels to []
    <Returns>
      True
    """
    # this must not fail -- it can however miss nodes that are offline
    # at the time when we are releasing them
    for v in vessels:
        try:
            success, ret = acquire_vessel(v, [])
        except:
            print "exception raised in release_vessels"
        else:
            if not success:
                print "release_vessels : " + str(ret)
    return True


def acquire_lan_vessels(geni_user, num):
    """
    <Purpose>
      Acquires num number of LAN vessels for user geni_user. All the
      acquired vessels are quaranteed to be in the same IP subnet. If
      there is no large enough subset of vessels that have the same
      subnet, this function fails and does not acquire any vessels for
      the user.
    <Arguments>
      geni_user:
        instance of User class for whom we are acquiring vessels
      num:
        number of vessels to acquire for the user
    <Exceptions>
      Not sure.
    <Side Effects>
      Performs a change users to geni_user on vessels acquired for the
      user.
    <Returns>
      On success, returns (True, (summary, explanation, acquired))
      where acquired is a list of vessels acquired for the geni
      user. On failure returns (False, (summary, explanation)). In
      boths cases, summary and explanation are strings that summarize
      and explains the success\failure in less/more detail. On
      failure, vessels that were acquired are released.
    """

    vessels = get_base_vessels(geni_user)

    summary = ""
    explanation = ""
    
    qry = """SELECT count(*) as cnt, subnet
             FROM control_donation
             GROUP BY subnet
             ORDER BY cnt DESC"""
    cursor = connection.cursor()
    cursor.execute(qry)
    rows = cursor.fetchall()
    if len(rows) == 0:
        summary = "No lan subnets"
        return False, (summary, explanation)

    for row in rows:
        cnt, subnet = row
        if cnt < num:
            explanation = summary = "Not enough LAN nodes available to acquire."
            return False, (summary, explanation)
        
        lan_vessels = vessels.filter(donation__subnet__exact=subnet)
        if lan_vessels.count() < num:
            continue
        
        # alpers - this is the start of parallelized acquisition
        # Attempts to acquire the the number of vessels left in each iteration of the while loop,
        # iterating again if the full number attempted is not achieved.
        acquired = []
        explanation = ""
        start_index = 0
        end_index = num
        while start_index < len(lan_vessels) and \
              end_index < len(lan_vessels):
            
            print "Trying to acquire " + str(num-len(acquired)) + \
                " vessels starting at index " + str(start_index)
            
            subset = lan_vessels[start_index : end_index]
            new_acquired, new_explanation = parallel_acquire_vessels(subset, geni_user)
            
            acquired.extend(new_acquired)
            explanation += " " + new_explanation
            
            # if all requested vessels have been acquired, flee the function
            if len(acquired) == num:
                return True, (summary, explanation, acquired)
            
            # otherwise, increase the lan_vessel index parameters based on the number of vessels
            # that were able to be acquired (start_index - end_index will be the number of vessels
            # attempted to be acquired on the next iteration)
            start_index += len(subset)
            end_index = start_index + num - len(acquired)
                
        # release all those vessels that were acquired
        # here and go to next subnet of hosts
        release_vessels(acquired)
                
    summary = str(len(rows)) + " Subnets available. Failed to acquire " + str(num) + " nodes in each subnet."
    return False, (summary, explanation)


def acquire_wan_vessels(geni_user, num):
    """
    <Purpose>
      Acquires num number of WAN vessels for user geni_user. This
      function guarantees that no two acquired vessels are in the same
      subnet. If the diversity of available resources do not permit
      this condition then the function fails and does not acquire any
      vessels for the user.
    <Arguments>
      geni_user:
        instance of User class for whom we are acquiring vessels
      num:
        number of vessels to acquire for the user
    <Exceptions>
      Not sure.
    <Side Effects>
      Performs a change users to geni_user on vessels acquired for the
      user.
    <Returns>
      On success, returns (True, (summary, explanation, acquired))
      where acquired is a list of vessels acquired for the geni
      user. On failure returns (False, (summary, explanation)). In
      boths cases, summary and explanation are strings that summarize
      and explains the success\failure in less/more detail. On
      failure, vessels that were acquired are released.
    """
    vessels = get_base_vessels(geni_user)
    
    qry = """SELECT distinct subnet
             FROM control_donation"""
    cursor = connection.cursor()
    cursor.execute(qry)
    rows = cursor.fetchall()
    summary = ""
    explanation = ""
    if len(rows) == 0:
        summary = "No donated resources are available."
        explanation = summary
        return False, (summary, explanation)

    # alpers - this is the start of parallelized acquisition
    acquired = []
    cnt = 0

    vessel_subnets = {}
    for row in rows:
        [subnet] = row
        print "working on populating subnet: " + str(subnet)
        donations = Donation.objects.filter(subnet=subnet)

        # try to grab all vessels (limit 10 artificially) in this subnet
        vessel_subnets[subnet] = []
        subnet_vessel_limit = 10
        for d in donations:
            subnet_vessels = vessels.filter(donation=d)
            if subnet_vessels.count() == 0:
                # a donation without any vessels -- strange?
                continue
            if len(vessel_subnets[subnet]) > subnet_vessel_limit:
                break
            else:
                vessel_subnets[subnet].extend(subnet_vessels)
            
        # Attempts to prevent function from populating a huge list that it will hardly use.
        # This line is super-suspect, although this saves the time of aggregating a list, it
        # *can* be possible that 2x the number of vessels requested can all fail.
        if len(vessel_subnets.keys()) > (num * 2):
            break

    # we've collected our collection of vessels, let's try to acquire some 
    while not len(vessel_subnets.keys()) < (num - len(acquired)):
        print "starting acquisition loop"
        vessels_to_submit = {}
        subnets_to_delete = []
        # populate our vessel subset, make another hash so we know which subnet each came from
        for k, v in vessel_subnets.iteritems():
            if len(vessels_to_submit.keys()) < (num - len(acquired)):
                # if a subnet has been exhausted of available vessels, remove it from the 
                # potential vessel source list
                if len(v) == 0:
                    subnets_to_delete.append(k)

                # otherwise, remove the specific vessel from the subnet and save it in the submission queue
                else:
                    vessels_to_submit[v.pop(0)] = k
            else:
                break

        # iteritems() doesn't like when keys are deleted in the middle of a loop, 
        # so vessel_subnets is clean up here
        for key in subnets_to_delete:
            del vessel_subnets[key]

        # submit jobs
        new_acquired, new_explanation = parallel_acquire_vessels(vessels_to_submit.keys(), geni_user)
        acquired.extend(new_acquired)

        if len(acquired) == num:
            print "acquired all num ok"
            return True, (summary, explanation, acquired)

        print "didn't find enough nodes (only " + str(len(acquired)) + "), retrying loop"
        
        # very important to ensure WAN case - remove the subnet from the list of available vessels
        for vessel in new_acquired:
            subnet = vessels_to_submit[vessel]
            del vessel_subnets[subnet]

    # otherwise, fall through
    release_vessels(acquired)
    summary = "Network diversity of available resources canot satisfy your request"
    explanation = "Cannot find diverse WAN resources to satisfy a request for " + str(num) + " vessels"
    return False, (summary, explanation)


def acquire_rand_vessels(geni_user, num):
    """
    <Purpose>
      Acquires num number of random vessels for user geni_user.
    <Arguments>
      geni_user:
        instance of User class for whom we are acquiring vessels
      num:
        number of vessels to acquire for the user
    <Exceptions>
      Not sure.
    <Side Effects>
      Performs a change users to geni_user on vessels acquired for the
      user.
    <Returns>
      On success, returns (True, (summary, explanation, acquired))
      where acquired is a list of vessels acquired for the geni
      user. On failure returns (False, (summary, explanation)). In
      boths cases, summary and explanation are strings that summarize
      and explains the success\failure in less/more detail. On
      failure, vessels that were acquired are released.
    """
    explanation = ""
    summary = ""
    
    # shuffle the base vessels set
    vessels = get_base_vessels(geni_user)
    vessels = list(vessels)
    random.shuffle(vessels)

    # alpers - this is the start of parallelized acquisition
    acquired = []
    explanation = ""
    start_index = 0
    end_index = num
    while start_index < len(vessels) and \
          end_index < len(vessels):
      
        print "Trying to acquire " + str(num-len(acquired)) + \
            " vessels starting at index " + str(start_index)
    
        subset = vessels[start_index : end_index]
        new_acquired, new_explanation = parallel_acquire_vessels(subset, geni_user)
    
        acquired.extend(new_acquired)
        explanation += " " + new_explanation

        # if all requested vessels have been acquired, flee the function
        if len(acquired) == num:
            summary = "Acquired all the nodes."
            return True, (summary, explanation, acquired)
    
        # otherwise, increase the vessel index parameters based on the number of vessels
        # that were able to be acquired and retry
        start_index += len(subset)
        end_index = start_index + num - len(acquired)

    release_vessels(acquired)
    explanation = str(len(vessels)) + " vessels available. In these, failed to acquire " + str(num) + " vessels."
    summary = "Failed to acquire nodes."
    return False, (summary, explanation)


def release_resources(geni_user, resource_id, all):
    """
    <Purpose>
      Releases either all resources (vesselmaps) or some specific
      resource for a geni user.
    <Arguments>
      geni_user:
        instance of the User class indicating the geni user
      resource_id (int):
        indicates the specific vessel map record to delete
      all (boolean):
        if True then deletes all vessel maps for the user
    <Exceptions>
      Not sure.
    <Side Effects>
      Deletes some number of vessel map entries associated with the geni_user.
    <Returns>
      If all is False, returns a string representation of the vessel
      that was removed. Otherwise returns an empty string
    """

    myresources = VesselMap.objects.filter(user=geni_user)

    ret = ""
    for r in myresources:
        if (all is True) or (r.id == resource_id):
            v = r.vessel_port.vessel
            nmip = v.donation.ip
            nmport = int(v.donation.port)
            vesselname = v.name
            nodepubkey = v.donation.owner_pubkey
            nodeprivkey = v.donation.owner_privkey
            success,msg = changeusers([""], nmip, nmport, vesselname, nodepubkey, nodeprivkey)
            if not success:
                print msg
            r.delete()
            if not all:
                ret = str(nmip) + ":" + str(nmport) + ":" + str(vesselname)
    return ret
            
@transaction.commit_manually    
def acquire_resources(geni_user, num, env_type):
    """
    <Purpose>
      Acquire num resources/vessels for usergeni_user of type env_type
      (LAN\WAN\Random).

    <Arguments>
      geni_user :
        A User class instance (see below) representing user for whom
        to acquire the vessels
      num :
        Number of vessels to acquire
      env_type :
        The type of vessel environment to acquire. Current support
        values are 1 : LAN, 2 : WAN, 3 : Random

    <Exceptions>
      None

    <Side Effects>
      Modifies the geni database to reflect new vessel
      assignments. Specifically, this function creates new VesselMap
      records and assigns vessels to users. This function also
      modifies vessel state by changing their user keys to geni_user's
      key.

    <Returns>
      bool, list where bool is True on success (some vessels
      acquired), False on failure (no vessels acquired). If bool is
      True then list is (acquired, explanation, summary) where
      acquired is the number of vesesls acquired, explanation is the
      detailed explanation of went on, and summary is a summary
      explanation of what went on. If bool is False then list is
      (explanation, summary) where explanation is a detailed
      explanation and summary is a summary explanation of why we
      failed.
    """
    explanation = ""
    summary = ""
    env_type_func_map = {1 : acquire_lan_vessels,
                         2 : acquire_wan_vessels,
                         3 : acquire_rand_vessels}
    try:
        num_available = geni_user.vessel_credit_remaining()
        if num > num_available:
            # user wants too much
            summary = "You do not have enough donations to acquire %d vessels"%(num)
            return False, (explanation, summary)

        # charge the user for requested resources
        geni_user.num_acquired_vessels += num

        if num == 1:
            acquire_func = acquire_rand_vessels
        else:
            acquire_func = env_type_func_map[int(env_type)]
        # attempt to acquire resources
        success, ret = acquire_func(geni_user, num)
        
        if not success:
            summary, explanation = ret
            explanation += "No more nodes available."
            transaction.rollback()
            return False, (explanation, summary)

        summary, explanation, acquired = ret
        ret = create_vmaps(acquired, geni_user)
        if not ret:
            release_vessels(acquired)
            raise "create_vmaps failed"
            

        #explanation += "There are  " + str(total_free_vessel_count) + " vessels free. Your port is available on " + str(len(vessels)) + " of them."
            
    except:
        transaction.rollback()
        # a hack to get the traceback information into a string by
        # printing to file and then reading back from file
        #traceback.print_tb(file=sys.stdout)
        summary += " Failed to acquire vessel(s). Internal Error. Please contact ivan@cs.washington.edu"
        summary += ''.join(traceback.format_exception(sys.exc_info()[0],sys.exc_info()[1],sys.exc_info()[2]))
        return False, (explanation, summary)
    else:
        transaction.commit()
        summary += " Acquired %d vessel(s). "%(num)
        return True, (num, explanation, summary)

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
          Returns the number of seconds remaining to the assignment of
          a user to a vessel
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
        delta = self.expiration - curr_time
        if delta.days == -1:
            ret = "now"
        else:
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

def test_acquire(username, num_nodes):
    """
    <Purpose>

    <Arguments>
        request:
            
        share_form:
            

    <Exceptions>
        

    <Side Effects>
        

    <Returns>
        
    """

    user = DjangoUser.objects.get(username=username)
    print "django user: ", user
    geni_user = User.objects.get(www_user = user)
    print "geni user: ", geni_user
    ret = acquire_resources(geni_user, num_nodes, "LAN")
    print "acquire returned: ", ret
    if ret[0] == False:
        print ret[1]

def test_acquire_node(username,nodeip,vesselname):
    """
    <Purpose>
        

    <Arguments>
        request:
            
        share_form:
            

    <Exceptions>
        

    <Side Effects>
        

    <Returns>
        
    """

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


from parallelvesselacquisition import parallel_acquire_vessels