""" 
Author: Justin Cappos

Module: Node Manager API.   This processes an already checked request.
    In almost all cases this means that no security checks are done here as
    a result.

Start date: September 1st, 2008

The design goals of this version are to be secure, simple, and reliable (in 
that order).   

The individual functions in here are called from nmrequesthandler.   The 
functions are listed in the API_dict.
"""

# used to persist data...
import persist

# used to do resource arithmatic magic...
import nmresourcemath

# Is this the same as nmrequesthandler.BadRequest?  (the expected type of 
# exception)
class BadRequest(Exception):
  pass

# used to check file names in addfiletovessel, retrievefilefromvessel, and
# deletefileinvessel
from emulfile import assert_is_allowed_filename

# needed for path.exists and remove
import os 

# needed for copy
import shutil

import threading

import subprocess

import time

# used in startvessel and stopvessel
import statusstorage

# used in startvessel and stopvessel
import nmstatusmonitor

# used to check file size restrictions...
import misc

# need this to check uploaded keys for validity
#begin include rsa.repy
"""RSA module

Adapted by Justin Cappos from the version by:
author = "Sybren Stuvel, Marloes de Boer and Ivo Tamboer"
date = "2008-04-23"


All of the base64 encoding, pickling, and zlib encoding has been removed
"""


# NOTE: Python's modulo can return negative numbers. We compensate for
# this behaviour using the abs() function

#begin include random.repy
""" Random routines (similar to random in Python)
Author: Justin Cappos


"""

def random_randint(minvalue, maxvalue):

  if minvalue > maxvalue:
    # mimic random's failure behaviour
    raise ValueError, "empty range for randrange()"

  if maxvalue == minvalue:
    return maxvalue

  randomrange = maxvalue - minvalue

  # get a small random number
  randomnumber = int(randomfloat() * 2**32)

  # We're going to generate the number 32 bits at a time...
  while randomrange > 2**32:
    # add random bits to the bottom...
    randomnumber = (randomnumber << 32) + int(randomfloat() * 2**32)
    # shift the range
    randomrange = randomrange >> 32

  # BUG: doing mod here isn't perfect.   If there are 32 bits to make random,
  # and the range isn't a power of 2, some numbers will be slightly more likely
  # than others...   I could detect and retry I guess...
  retvalue = minvalue + (randomnumber % (maxvalue - minvalue + 1))
  assert(minvalue<=retvalue<=maxvalue)
  return retvalue


def random_sample(population, k):
  newpopulation = population[:]
  if len(population) < k:
    raise ValueError, "sample larger than population"

  retlist = []
  populationsize = len(population)-1

  for num in range(k):
    pos = random_randint(0,populationsize-num)
    retlist.append(newpopulation[pos])
    del newpopulation[pos]

  return retlist
#end include random.repy

#begin include math.repy
""" Justin Cappos -- substitute for a few python math routines"""

def math_ceil(x):
  xint = int(x)
  
  # if x is positive and not equal to itself truncated then we should add 1
  if x > 0 and x != xint:
    xint = xint + 1

  # I return a float because math.ceil does
  return float(xint)



def math_floor(x):
  xint = int(x)
  
  # if x is negative and not equal to itself truncated then we should subtract 1
  if x < 0 and x != xint:
    xint = xint - 1

  # I return a float because math.ceil does
  return float(xint)



math_e = 2.7182818284590451
math_pi = 3.1415926535897931

# stolen from a link off of wikipedia (http://en.literateprograms.org/Logarithm_Function_(Python)#chunk use:logN.py)
# MIT license
#
# hmm, math_log(4.5,4)      == 1.0849625007211561
# Python's math.log(4.5,4)  == 1.0849625007211563
# I'll assume this is okay.
def math_log(X, base=math_e, epsilon=1e-16):
  # log is logarithm function with the default base of e
  integer = 0
  if X < 1 and base < 1:
    # BUG: the cmath implementation can handle smaller numbers...
    raise ValueError, "math domain error"
  while X < 1:
    integer -= 1
    X *= base
  while X >= base:
    integer += 1
    X /= base
  partial = 0.5               # partial = 1/2 
  X *= X                      # We perform a squaring
  decimal = 0.0
  while partial > epsilon:
    if X >= base:             # If X >= base then a_k is 1 
      decimal += partial      # Insert partial to the front of the list
      X = X / base            # Since a_k is 1, we divide the number by the base
    partial *= 0.5            # partial = partial / 2
    X *= X                    # We perform the squaring again
  return (integer + decimal)

#end include math.repy



def rsa_gcd(p, q):
    """Returns the greatest common divisor of p and q


    >>> gcd(42, 6)
    6
    """
    if p<q: return rsa_gcd(q, p)
    if q == 0: return p
    return rsa_gcd(q, abs(p%q))

def rsa_bytes2int(bytes):
    """Converts a list of bytes or a string to an integer

    >>> (128*256 + 64)*256 + + 15
    8405007
    >>> l = [128, 64, 15]
    >>> bytes2int(l)
    8405007
    """

    if not (type(bytes) is list or type(bytes) is str):
        raise TypeError("You must pass a string or a list")

    # there is a bug here that strings with leading \000 have the leading char
    # stripped away.   I need to fix that.  To fix it, I prepend \001 to 
    # everything I process.   I also have to ensure I'm passed a small enough
    # chunk that it all still fits (fix for that where I'm called).
    bytes = '\001' + bytes

    # Convert byte stream to integer
    integer = 0
    for byte in bytes:
        integer *= 256
        # this used to be StringType which includes unicode, however, this
        # loop doesn't correctly handle unicode data, so the change should also
        # be a bug fix
        if type(byte) is str: byte = ord(byte)
        integer += byte

    return integer

def rsa_int2bytes(number):
    """Converts a number to a string of bytes
    
    >>> bytes2int(int2bytes(123456789))
    123456789
    """

    if not (type(number) is long or type(number) is int):
        raise TypeError("You must pass a long or an int")

    string = ""

    while number > 0:
        string = "%s%s" % (chr(number & 0xFF), string)
        number /= 256
    
    if string[0] != '\001':
        raise TypeError("Invalid RSA data")
 
    return string[1:]

def rsa_fast_exponentiation(a, p, n):
    """Calculates r = a^p mod n
    """
    result = a % n
    remainders = []
    while p != 1:
        remainders.append(p & 1)
        p = p >> 1
    while remainders:
        rem = remainders.pop()
        result = ((a ** rem) * result ** 2) % n
    return result

def rsa_fermat_little_theorem(p):
    """Returns 1 if p may be prime, and something else if p definitely
    is not prime"""

    a = random_randint(1, p-1)
    return rsa_fast_exponentiation(a, p-1, p)

def rsa_jacobi(a, b):
    """Calculates the value of the Jacobi symbol (a/b)
    """

    if a % b == 0:
        return 0
    result = 1
    while a > 1:
        if a & 1:
            if ((a-1)*(b-1) >> 2) & 1:
                result = -result
            b, a = a, b % a
        else:
            if ((b ** 2 - 1) >> 3) & 1:
                result = -result
            a = a >> 1
    return result

def rsa_jacobi_witness(x, n):
    """Returns False if n is an Euler pseudo-prime with base x, and
    True otherwise.
    """

    j = rsa_jacobi(x, n) % n
    f = rsa_fast_exponentiation(x, (n-1)/2, n)

    if j == f: return False
    return True

def rsa_randomized_primality_testing(n, k):
    """Calculates whether n is composite (which is always correct) or
    prime (which is incorrect with error probability 2**-k)

    Returns False if the number if composite, and True if it's
    probably prime.
    """

    q = 0.5     # Property of the jacobi_witness function

    t = int(math_ceil(k / math_log(1/q, 2)))
    for junk in range(t+1):
        # JAC: Sometimes we get a ValueError here because the range is empty 
        # (i.e. we are doing randint(1,1) or randint (1,0), etc.).   I'll check
        # and return False in this case and declare 1 and 2 composite (since 
        # they make horrible p or q in RSA).
        if n-1 < 2:
          return False
        x = random_randint(1, n-1)
        if rsa_jacobi_witness(x, n): return False
    
    return True

def rsa_is_prime(number):
    """Returns True if the number is prime, and False otherwise.

    >>> rsa_is_prime(42)
    0
    >>> rsa_is_prime(41)
    1
    """

    """
    if not fermat_little_theorem(number) == 1:
        # Not prime, according to Fermat's little theorem
        return False
    """

    if rsa_randomized_primality_testing(number, 5):
        # Prime, according to Jacobi
        return True
    
    # Not prime
    return False

    
def rsa_getprime(nbits):
    """Returns a prime number of max. 'math_ceil(nbits/8)*8' bits. In
    other words: nbits is rounded up to whole bytes.

    >>> p = getprime(8)
    >>> rsa_is_prime(p-1)
    0
    >>> rsa_is_prime(p)
    1
    >>> rsa_is_prime(p+1)
    0
    """

    while True:
#        integer = read_random_int(nbits)
        integer = random_randint(1,2**nbits)

        # Make sure it's odd
        integer |= 1

        # Test for primeness
        if rsa_is_prime(integer): break

        # Retry if not prime

    return integer

def rsa_are_relatively_prime(a, b):
    """Returns True if a and b are relatively prime, and False if they
    are not.

    >>> are_relatively_prime(2, 3)
    1
    >>> are_relatively_prime(2, 4)
    0
    """

    d = rsa_gcd(a, b)
    return (d == 1)

def rsa_find_p_q(nbits):
    """Returns a tuple of two different primes of nbits bits"""

    p = rsa_getprime(nbits)
    while True:
        q = rsa_getprime(nbits)
        if not q == p: break
    
    return (p, q)

def rsa_extended_euclid_gcd(a, b):
    """Returns a tuple (d, i, j) such that d = gcd(a, b) = ia + jb
    """

    if b == 0:
        return (a, 1, 0)

    q = abs(a % b)
    r = long(a / b)
    (d, k, l) = rsa_extended_euclid_gcd(b, q)

    return (d, l, k - l*r)

# Main function: calculate encryption and decryption keys
def rsa_calculate_keys(p, q, nbits):
    """Calculates an encryption and a decryption key for p and q, and
    returns them as a tuple (e, d)"""

    n = p * q
    phi_n = (p-1) * (q-1)

    while True:
        # Make sure e has enough bits so we ensure "wrapping" through
        # modulo n
        e = rsa_getprime(max(8, nbits/2))
        if rsa_are_relatively_prime(e, n) and rsa_are_relatively_prime(e, phi_n): break

    (d, i, j) = rsa_extended_euclid_gcd(e, phi_n)

    if not d == 1:
        raise Exception("e (%d) and phi_n (%d) are not relatively prime" % (e, phi_n))

    if not (e * i) % phi_n == 1:
        raise Exception("e (%d) and i (%d) are not mult. inv. modulo phi_n (%d)" % (e, i, phi_n))

    return (e, i)


def rsa_gen_keys(nbits):
    """Generate RSA keys of nbits bits. Returns (p, q, e, d).
    """

    while True:
        (p, q) = rsa_find_p_q(nbits)
        (e, d) = rsa_calculate_keys(p, q, nbits)

        # For some reason, d is sometimes negative. We don't know how
        # to fix it (yet), so we keep trying until everything is shiny
        if d > 0: break

    return (p, q, e, d)

def rsa_gen_pubpriv_keys(nbits):
    """Generates public and private keys, and returns them as (pub,
    priv).

    The public key consists of a dict {e: ..., , n: ....). The private
    key consists of a dict {d: ...., p: ...., q: ....).
    """
    
    (p, q, e, d) = rsa_gen_keys(nbits)

    return ( {'e': e, 'n': p*q}, {'d': d, 'p': p, 'q': q} )


def rsa_encrypt_int(message, ekey, n):
    """Encrypts a message using encryption key 'ekey', working modulo
    n"""

    if type(message) is int:
        return rsa_encrypt_int(long(message), ekey, n)

    if not type(message) is long:
        raise TypeError("You must pass a long or an int")

    if math_floor(math_log(message, 2)) > math_floor(math_log(n, 2)):
        raise OverflowError("The message is too long")

    return rsa_fast_exponentiation(message, ekey, n)

def rsa_decrypt_int(cyphertext, dkey, n):
    """Decrypts a cypher text using the decryption key 'dkey', working
    modulo n"""

    return rsa_encrypt_int(cyphertext, dkey, n)

def rsa_sign_int(message, dkey, n):
    """Signs 'message' using key 'dkey', working modulo n"""

    return rsa_decrypt_int(message, dkey, n)

def rsa_verify_int(signed, ekey, n):
    """verifies 'signed' using key 'ekey', working modulo n"""

    return rsa_encrypt_int(signed, ekey, n)

def rsa_picklechops(chops):
    """previously used to pickles and base64encodes it's argument chops"""

    retstring = ''
    for item in chops:
      retstring = retstring + ' ' + str(item)
    return retstring

def rsa_unpicklechops(string):
    """previously used to base64decode and unpickle it's argument string"""

    retchops = []
    for item in string.split():
      retchops.append(long(item))
    return retchops

def rsa_chopstring(message, key, n, funcref):
    """Splits 'message' into chops that are at most as long as n,
    converts these into integers, and calls funcref(integer, key, n)
    for each chop.

    Used by 'encrypt' and 'sign'.
    """

    msglen = len(message)
    nbits = int(math_floor(math_log(n, 2)))
    # JAC: subtract a byte because we're going to add an extra char on the front
    # to properly handle leading \000 bytes
    nbytes = int(nbits / 8)-1
    blocks = int(msglen / nbytes)

    if msglen % nbytes > 0:
        blocks += 1

    cypher = []
    
    for bindex in range(blocks):
        offset = bindex * nbytes
        block = message[offset:offset+nbytes]
        value = rsa_bytes2int(block)
        cypher.append(funcref(value, key, n))

    return rsa_picklechops(cypher)

def rsa_gluechops(chops, key, n, funcref):
    """Glues chops back together into a string.  calls
    funcref(integer, key, n) for each chop.

    Used by 'decrypt' and 'verify'.
    """
    message = ""

    chops = rsa_unpicklechops(chops)
    
    for cpart in chops:
        mpart = funcref(cpart, key, n)
        message += rsa_int2bytes(mpart)
    
    return message

def rsa_encrypt(message, key):
    """Encrypts a string 'message' with the public key 'key'"""
    
    return rsa_chopstring(message, key['e'], key['n'], rsa_encrypt_int)

def rsa_sign(message, key):
    """Signs a string 'message' with the private key 'key'"""
    
    return rsa_chopstring(message, key['d'], key['p']*key['q'], rsa_decrypt_int)

def rsa_decrypt(cypher, key):
    """Decrypts a cypher with the private key 'key'"""

    return rsa_gluechops(cypher, key['d'], key['p']*key['q'], rsa_decrypt_int)

def rsa_verify(cypher, key):
    """Verifies a cypher with the public key 'key'"""

    return rsa_gluechops(cypher, key['e'], key['n'], rsa_encrypt_int)


def rsa_is_valid_privatekey(key):
    """This tries to determine if a key is valid.   If it returns False, the
       key is definitely invalid.   If True, the key is almost certainly valid"""
    # must be a dict
    if type(key) is not dict:
        return False

    # missing the right keys
    if 'd' not in key or 'p' not in key or 'q' not in key:
        return False

    # has extra data in the key
    if len(key) != 3:
        return False

    for item in ['d', 'p', 'q']:
        # must have integer or long types for the key components...
        if type(key[item]) is not int and type(key[item]) is not long:
            return False

    if rsa_is_prime(key['p']) and rsa_is_prime(key['q']):
        # Seems valid...
        return True
    else:
        return False
  

def rsa_is_valid_publickey(key):
    """This tries to determine if a key is valid.   If it returns False, the
       key is definitely invalid.   If True, the key is almost certainly valid"""
    # must be a dict
    if type(key) is not dict:
        return False

    # missing the right keys
    if 'e' not in key or 'n' not in key:
        return False

    # has extra data in the key
    if len(key) != 2:
        return False

    for item in ['e', 'n']:
        # must have integer or long types for the key components...
        if type(key[item]) is not int and type(key[item]) is not long:
            return False

    if key['e'] < key['n']:
        # Seems valid...
        return True
    else:
        return False
  

def rsa_publickey_to_string(key):
  if not rsa_is_valid_publickey(key):
    raise ValueError, "Invalid public key"

  return str(key['e'])+" "+str(key['n'])


def rsa_string_to_publickey(mystr):
  if len(mystr.split()) != 2:
    raise ValueError, "Invalid public key string"

  
  return {'e':long(mystr.split()[0]), 'n':long(mystr.split()[1])}



def rsa_privatekey_to_string(key):
  if not rsa_is_valid_privatekey(key):
    raise ValueError, "Invalid private key"

  return str(key['d'])+" "+str(key['p'])+" "+str(key['q'])


def rsa_string_to_privatekey(mystr):
  if len(mystr.split()) != 3:
    raise ValueError, "Invalid private key string"

  
  return {'d':long(mystr.split()[0]), 'p':long(mystr.split()[1]), 'q':long(mystr.split()[2])}


def rsa_privatekey_to_file(key,filename):
  if not rsa_is_valid_privatekey(key):
    raise ValueError, "Invalid private key"

  fileobject = file(filename,"w")
  fileobject.write(rsa_privatekey_to_string(key))
  fileobject.close()



def rsa_file_to_privatekey(filename):
  fileobject = file(filename,'r')
  privatekeystring = fileobject.read()
  fileobject.close()

  return rsa_string_to_privatekey(privatekeystring)



def rsa_publickey_to_file(key,filename):
  if not rsa_is_valid_publickey(key):
    raise ValueError, "Invalid public key"

  fileobject = file(filename,"w")
  fileobject.write(rsa_publickey_to_string(key))
  fileobject.close()



def rsa_file_to_publickey(filename):
  fileobject = file(filename,'r')
  publickeystring = fileobject.read()
  fileobject.close()

  return rsa_string_to_publickey(publickeystring)




#end include rsa.repy
# MIX: fix with repy <-> python integration changes
import random
randomfloat = random.random()

offcutfilename = "resources.offcut"

# The node information (reported to interested clients)
nodename = ""
nodepubkey = ""
nodeversion = ''

# the maximum size the logging buffer can be
# NOTE: make sure this is equal to the maxbuffersize in logging.py
logmaxbuffersize = 16*1024

# the maximum length of the ownerstring
maxownerstringlength = 256


# The vesseldict is the heart and soul of the node manager.   It keeps all of 
# the important state for the node.   The functions that change this must 
# persist it afterwards.
# The format of an entry is:
#   'vesselname':{'userkeys':[key1, key2, ...], 'ownerkey':key, 
#   'oldmetadata':info, 'stopfilename':stopfile, 'logfilename':logfile, 
#   'advertise':True, 'ownerinformation':'...', 'status':'Fresh',
#   'resourcefilename':resourcefilename, 'statusfilename':statusfilename}
#
# The 'status' field is updated by the status monitor.   This thread only 
# reads it.
# 
# The 'advertise' field is read by the advertise thread.   This thread updates
# the value.
#
# The stopfilename is always the vesselname+'.stop', the logfilename is always 
# the vesselname+'.log', and the resourcefilename is 'resources.'+vesselname
# However, these are listed in the dictionary rather than derived when needed
# for clarity / ease of future changes.
#
# No item that is modified by an API call requires persistant updates to
# anything except the vesseldict.   The vesseldict must always be the
# last thing to be updated.   Since all actions that are performed on existing
# files are either atomic or read-only, there is no danger of corruption of
# the disk state.
vesseldict = {}


def initialize(name, pubkey, version):
  # Need to set the node name, etc. here...
  global nodename
  global nodepubkey
  global nodeversion
  global vesseldict
  

  nodename = name
  nodepubkey = pubkey

  nodeversion = version 

  # load the vessel from disk
  vesseldict = persist.restore_object('vesseldict')

  return vesseldict


def getvessels():
  # Returns vessel information
  # start with the node name, etc.
  vesselstring = "Version: "+nodeversion+"\n"
  vesselstring = vesselstring+"Nodename: "+nodename+"\n"
  vesselstring = vesselstring+"Nodekey: "+rsa_publickey_to_string(nodepubkey)+"\n"
  
  # for each vessel add name, status ownerkey, ownerinfo, userkey(s)
  for vesselname in vesseldict:
    vesselstring = vesselstring+"Name: "+vesselname+"\n"
    vesselstring = vesselstring+"Status: "+vesseldict[vesselname]['status']+"\n"
    vesselstring = vesselstring+"Advertise: "+str(vesseldict[vesselname]['advertise'])+"\n"
    vesselstring = vesselstring+"OwnerKey: "+rsa_publickey_to_string(vesseldict[vesselname]['ownerkey'])+"\n"
    vesselstring = vesselstring+"OwnerInfo: "+vesseldict[vesselname]['ownerinformation']+"\n"
    for userkey in vesseldict[vesselname]['userkeys']:
      vesselstring = vesselstring+"UserKey: "+rsa_publickey_to_string(userkey)+"\n"

  vesselstring = vesselstring + "\nSuccess"
  return vesselstring


def getvesselresources(vesselname):

  if vesselname not in vesseldict:
    raise BadRequest, "No such vessel"

  # return the resources file...
  resourcefo = open(vesseldict[vesselname]['resourcefilename'])
  resourcedata = resourcefo.read()
  resourcefo.close()
  resourcedata = resourcedata + "\nSuccess"
  return resourcedata

def getoffcutresources():
  # return the resources file...
  resourcefo = open(offcutfilename)
  resourcedata = resourcefo.read()
  resourcefo.close()
  resourcedata = resourcedata + "\nSuccess"
  return resourcedata


allowedchars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890.-_ "

def startvessel(vesselname, argstring):
  if vesselname not in vesseldict:
    raise BadRequest, "No such vessel"

  if vesseldict[vesselname]['status'] == 'Started':
    raise BadRequest("Vessel has already been started")

  # remove any prior stop file so that we can start
  if os.path.exists(vesseldict[vesselname]['stopfilename']):
    os.remove(vesseldict[vesselname]['stopfilename'])

  for char in argstring:
    if char not in allowedchars:
      raise BadRequest("Character '"+char+"' not allowed in arguments")
 
  # I'm going to capture the status and timestamp and then check the see if
  # the timestamp is updated...
  oldstatus, oldtimestamp = statusstorage.read_status(vesseldict[vesselname]['statusfilename'])

  # fixing a bug (thanks Brent!) that I was in the wrong directory when 
  # writing files...

  # change directory so that the sandboxes current directory is in its dir...
  os.chdir(vesselname)

  # ... but always reset it...
  try:
    # architecturally, I'm unsure prepending ../ is the best solution...
    commandstring = "python ../repy.py --logfile ../"+vesseldict[vesselname]['logfilename']+" --stop ../"+vesseldict[vesselname]['stopfilename']+" --status ../"+vesseldict[vesselname]['statusfilename']+" ../"+vesseldict[vesselname]['resourcefilename']+" "+argstring

    start_task(commandstring)

  finally:
    # reset the path
    os.chdir('..')

  starttime = time.time()

  # wait for 10 seconds for it to start (else return an error)
  while time.time()-starttime < 10:
    newstatus, newtimestamp = statusstorage.read_status(vesseldict[vesselname]['statusfilename'])
    # Great!   The timestamp was updated...   The new status is the result of 
    # our work.   Let's tell the user what happened...
    if newtimestamp != oldtimestamp and newstatus != None:
      break

    # sleep while busy waiting...
    time.sleep(.5)

  else:
    return "Did not start in a timely manner\nWarning"

  # We need to update the status in the table because the status thread might
  # not notice this before our next request... (else occasional failures on XP)
  nmstatusmonitor.update_status(vesseldict, vesselname, newstatus, newtimestamp)


  return newstatus+"\nSuccess"



# A helper for startvessel.   private to this module
def start_task(command):
 
  # Should I use call here?
  subprocess.Popen(command, shell=True)


def stopvessel(vesselname):
  if vesselname not in vesseldict:
    raise BadRequest, "No such vessel"

  # this is broken out to prevent a race between checking the status and 
  # reporting the error
  currentstatus = vesseldict[vesselname]['status'] 
  # It must be started for us to stop it...
  if currentstatus != 'Started':
    raise BadRequest("Cannot stop vessel with status '"+currentstatus+"'")
  
  # create the stop file
  open(vesseldict[vesselname]['stopfilename'],"w").close()

  starttime = time.time()

  # wait for up to 10 seconds for it to stop (else return an error)
  while time.time()-starttime < 10:
    if vesseldict[vesselname]['status'] != 'Started':
      break

    # sleep while busy waiting...
    time.sleep(.5)

  else:
    return "May not have stopped in a timely manner\nWarning"
  
  return vesseldict[vesselname]['status']+"\nSuccess"
  


# Create a file in the vessel
def addfiletovessel(vesselname,filename, filedata):
  if vesselname not in vesseldict:
    raise BadRequest, "No such vessel"

  # get the current amount of data used by the vessel...
  currentsize = misc.compute_disk_use(vesselname+"/")
  # ...and the allowed amount
  resourcedata = nmresourcemath.read_resources_from_file(vesseldict[vesselname]['resourcefilename'])

  # If the current size + the size of the new data is too large, then deny
  if currentsize + len(filedata) > resourcedata['diskused']:
    raise BadRequest("Not enough free disk space")
  
  try:
    assert_is_allowed_filename(filename)
  except TypeError, e:
    raise BadRequest(str(e))

  writefo = open(vesselname+"/"+filename,"w")
  writefo.write(filedata)
  writefo.close()

  return "\nSuccess"
  


# Return a file from the vessel
def retrievefilefromvessel(vesselname,filename):
  if vesselname not in vesseldict:
    raise BadRequest, "No such vessel"

  try:
    assert_is_allowed_filename(filename)
  except TypeError, e:
    raise BadRequest(str(e))

  try:
    readfo = open(vesselname+"/"+filename)
  except IOError, e:
    # file not found!   Let's detect and re-raise
    if e[0] == 2:
      return "Error, File Not Found\nError"
    
    # otherwise re-raise the error
    raise

  filedata = readfo.read()
  readfo.close()

  return filedata + "\nSuccess"
  


# Delete a file in the vessel
def deletefileinvessel(vesselname,filename):
  if vesselname not in vesseldict:
    raise BadRequest, "No such vessel"
  
  try:
    assert_is_allowed_filename(filename)
  except TypeError, e:
    raise BadRequest(str(e))

  if not os.path.exists(vesselname+"/"+filename):
    raise BadRequest("File not found")

  os.remove(vesselname+"/"+filename)

  return "\nSuccess"
  

# Read the log file for the vessel
def readvessellog(vesselname):
  if vesselname not in vesseldict:
    raise BadRequest, "No such vessel"
  # copy the files, read the files, delete the copies.   
  # BUG: I don't believe there is a way to do this without any possibility for
  # race conditions (since copying two files is not atomic) without modifying
  # the sandbox to coordinate locking with the node manager
  

  # I'll use this to track if it fails or not.   This flag is used (instead of
  # doing the actual work) to minimize the time between copy calls.
  firstOK=False
  try:
    shutil.copy(vesseldict[vesselname]['logfilename']+'.old', "tmplog")
  except IOError, e:
    if e[0] == 2:
      # No such file or directory, we should ignore (we likely interrupted an 
      # non-atomic move)...
      pass
    else:
      raise
  else:
    firstOK = True


  secondOK = False
  # I have this next so that the amount of time between copying the files is 
  # minimized (I'll read both after)
  try:
    shutil.copy(vesseldict[vesselname]['logfilename']+'.new', "tmplog.new")
  except IOError, e:
    if e[0] == 2:
      # No such file or directory, we should ignore (we likely interrupted an 
      # non-atomic move)...
      pass
    else:
      raise
  else:
    secondOK = True


  # the log from the vessel
  readstring = ""

  # read the data and remove the files.
  if firstOK:
    readfo = open("tmplog")
    readstring = readstring + readfo.read()
    readfo.close()
    os.remove("tmplog")
    
  # read the data and remove the files.
  if secondOK:
    readfo = open("tmplog.new")
    readstring = readstring + readfo.read()
    readfo.close()
    os.remove("tmplog.new")

  # return only the last 16KB (hide the fact more may be stored)
  # NOTE: Should we return more?   We have more data...
  return readstring[-logmaxbuffersize:]+"\nSuccess"
  


def changeowner(vesselname, newkeystring):
  if vesselname not in vesseldict:
    raise BadRequest, "No such vessel"
  try:
    newkey = rsa_string_to_publickey(newkeystring)
  except ValueError:
    raise BadRequest("Invalid Key String")
    
  # check the key 
  if not rsa_is_valid_publickey(newkey):
    raise BadRequest("Invalid Key")

  vesseldict[vesselname]['ownerkey'] = newkey 

  # Must reset the owner information because it's used for service security.
  vesseldict[vesselname]['ownerinformation'] = ''

  # Reset the advertise flag so the owner can find the node...
  vesseldict[vesselname]['advertise'] = True

  persist.commit_object(vesseldict, "vesseldict")
  return "\nSuccess"
  

def changeusers(vesselname, listofkeysstring):
  if vesselname not in vesseldict:
    raise BadRequest, "No such vessel"
  newkeylist = []

  # check the keys
  for keystring in listofkeysstring.split('|'):
    if keystring == '':
      continue

    try:
      newkey = rsa_string_to_publickey(keystring)
    except ValueError:
      raise BadRequest("Invalid Key String '"+keystring+"'")

    if not rsa_is_valid_publickey(newkey):
      raise BadRequest("Invalid Key '"+keystring+"'")
    
    newkeylist.append(newkey)

  vesseldict[vesselname]['userkeys'] = newkeylist
    
  persist.commit_object(vesseldict, "vesseldict")
  return "\nSuccess"

def changeownerinformation(vesselname, ownerstring):
  if vesselname not in vesseldict:
    raise BadRequest, "No such vessel"
  if len(ownerstring) > maxownerstringlength:
    raise BadRequest("String Too Long")

  if '\n' in ownerstring:
    raise BadRequest("String may not contain newline character")

  vesseldict[vesselname]['ownerinformation'] = ownerstring

  persist.commit_object(vesseldict, "vesseldict")
  return "\nSuccess"
  


# NOTE: Should this be something other than True / False (perhaps owner / user /
# none?)
def changeadvertise(vesselname, setting):
  if vesselname not in vesseldict:
    raise BadRequest, "No such vessel"
  if setting == 'True':
    vesseldict[vesselname]['advertise'] = True
  elif setting == 'False':
    vesseldict[vesselname]['advertise'] = False
  else: 
    raise BadRequest("Invalid advertisement setting '"+setting+"'")

  persist.commit_object(vesseldict, "vesseldict")
  return "\nSuccess"


lastusednumber = None

# private.   A helper function that returns an unused vessel name
def get_new_vessel_name():
  global lastusednumber
  if lastusednumber == None:
    # let's look at the dictionary and figure something out
    maxval = 0
    for vesselname in vesseldict:
      # I'm assuming naming is done by 'v'+number
      assert(vesselname[0] == 'v')
      maxval = max(maxval, int(vesselname[1:]))
  
    lastusednumber = maxval

  lastusednumber = lastusednumber + 1
  return 'v'+str(lastusednumber)




# Private.   Creates a new vessel's state in the dictionary and on disk
def setup_vessel(vesselname, examplevessel):
  if vesselname in vesseldict:
    raise Exception, "Internal Error, setting up vessel '"+vesselname+"' already in vesseldict"

  # Set the invariants up...
  item = {}
  item['stopfilename'] = vesselname+".stop"
  item['logfilename'] = vesselname+".log"
  item['resourcefilename'] = "resource."+vesselname
  item['status'] = 'Fresh'
  item['statusfilename'] = vesselname+".status"

  # first the easy stuff...   Set up the vesseldict dictionary
  if examplevessel == None:
    item['userkeys'] = []
    item['ownerkey'] = {}
    item['oldmetadata'] = None
    item['advertise'] = True
    item['ownerinformation'] = ''

  else:
    if examplevessel not in vesseldict:
      raise Exception, "Internal Error, examplevessel '"+examplevessel+"' not in vesseldict"

    item['userkeys'] = vesseldict[examplevessel]['userkeys']
    item['ownerkey'] = vesseldict[examplevessel]['ownerkey']
    item['oldmetadata'] = vesseldict[examplevessel]['oldmetadata']
    item['advertise'] = vesseldict[examplevessel]['advertise']
    item['ownerinformation'] = vesseldict[examplevessel]['ownerinformation']

    # let's copy restrictions from the other vessel...

    # get the old restrictions...
    resourcefo = open(vesseldict[examplevessel]['resourcefilename'])
    restrictionsdata = resourcefo.read()
    resourcefo.close()
    restrictionsstring = nmresourcemath.read_restrictionsstring_from_data(restrictionsdata)

    # append to the resource file...
    outfo = open(item['resourcefilename'],"a")
    outfo.write(restrictionsstring)
    outfo.close()

  # create the directory on the file system
  os.mkdir(vesselname)

  # now we're ready to add the entry to the table (so other threads can use it)
  vesseldict[vesselname] = item

    

# Private
# BUG: What about a running vessel?
def destroy_vessel(vesselname):
  if vesselname not in vesseldict:
    raise Exception, "Internal Error, destroying a non-existant vessel '"+vesselname+"'"

  # remove the entry first so other threads aren't confused
  item = vesseldict[vesselname]
  del vesseldict[vesselname]


  shutil.rmtree(vesselname)
  if os.path.exists(item['logfilename']):
    os.remove(item['logfilename'])
  if os.path.exists(item['logfilename']+".new"):
    os.remove(item['logfilename']+".new")
  if os.path.exists(item['logfilename']+".old"):
    os.remove(item['logfilename']+".old")

  if os.path.exists(item['stopfilename']):
    os.remove(item['stopfilename'])

  if os.path.exists(item['resourcefilename']):
    os.remove(item['resourcefilename'])



def splitvessel(vesselname, resourcedata):
  if vesselname not in vesseldict:
    raise BadRequest, "No such vessel"
  
  if vesseldict[vesselname]['status'] == 'Started':
    raise BadRequest("Attempting to split a running vessel")

  # get the new name
  newname1 = get_new_vessel_name()
  newname2 = get_new_vessel_name()

  resourcefo = open("resource.temp","w")
  resourcefo.write(resourcedata)
  resourcefo.close()
  
  try:
    nmresourcemath.split(vesseldict[vesselname]['resourcefilename'], "resource.temp", offcutfilename, "resource."+newname1)

  except nmresourcemath.ResourceParseError, e:
    os.remove("resource.temp")
    raise BadRequest(str(e))

  os.rename("resource.temp","resource."+newname2)
  setup_vessel(newname1, vesselname)
  setup_vessel(newname2, vesselname)
  destroy_vessel(vesselname)
    
  persist.commit_object(vesseldict, "vesseldict")
  return newname1+" "+newname2+"\nSuccess"

    
  
  

def joinvessels(vesselname1, vesselname2):
  if vesselname1 not in vesseldict:
    raise BadRequest, "No such vessel '"+vesselname1+"'"
  if vesselname2 not in vesseldict:
    raise BadRequest, "No such vessel '"+vesselname2+"'"

  if vesseldict[vesselname1]['ownerkey'] != vesseldict[vesselname2]['ownerkey']:
    raise BadRequest("Vessels must have the same owner")
  
  if vesseldict[vesselname1]['status'] == 'Started' or vesseldict[vesselname2]['status'] == 'Started':
    raise BadRequest("Attempting to join a running vessel")
  
  # get the new name
  newname = get_new_vessel_name()

  nmresourcemath.combine(vesseldict[vesselname1]['resourcefilename'], vesseldict[vesselname2]['resourcefilename'], offcutfilename, "resource."+newname)

  setup_vessel(newname, vesselname1)
  destroy_vessel(vesselname1)
  destroy_vessel(vesselname2)
    
  persist.commit_object(vesseldict, "vesseldict")
  return newname+"\nSuccess"

    

def setrestrictions(vesselname, restrictionsdata):
  if vesselname not in vesseldict:
    raise BadRequest, "No such vessel '"+vesselname1+"'"

  if vesseldict[vesselname]['status'] == 'Started':
    raise BadRequest("Attempting to SetRestrictions for a running vessel")
  
  # Now we read the resources for the vessel...
  resourcedata = nmresourcemath.read_resources_from_file(vesseldict[vesselname]['resourcefilename'])
 
  # I think that all we really want to do is write out the restrictions file 
  # (assuming it contains no resource entries)...

  restrictionsstring = nmresourcemath.read_restrictionsstring_from_data(restrictionsdata)

  # write the new file...
  nmresourcemath.write_resource_dict(resourcedata, "resource.temp")
  outfo = open("resource.temp","a")
  outfo.write(restrictionsstring)
  outfo.close()
 
  os.remove(vesseldict[vesselname]['resourcefilename'])
  os.rename("resource.temp",vesseldict[vesselname]['resourcefilename'])
  
  return "\nSuccess"

    






