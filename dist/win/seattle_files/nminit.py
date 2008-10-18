""" 
Author: Justin Cappos

Module: Node Manager initializer.   It initializes the state needed to run the
        node manager on the local node.   This would most likely be run by the
        installer.

Start date: September 10rd, 2008

This initializes the node manager for Seattle.   It sets up the starting 
resources, creates a configuration file, etc.

The design goals of this version are to be secure, simple, and reliable (in 
that order).   

"""

# need to generate a public key
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

# need randomfloat...
import random
randomfloat = random.random


import os

import persist

# embedded here.   Is this really the right thing to do?
justinpubkey = {'e':90828751313604138861138199375516065418794160799843599128558705100285394924191002288444206024669046851496823164408997538063597164575888556545759466459359562498107740756089920043807948902332473328246320686052784108549174961107584377257390484702552802720358211058670482304929480676775120529587723588725818443641, 'n':525084957612029403526131505174200975825703127251864132403159502859804160822964990468591281636411242654674747961575351961726000088901250174303367500864513464050509705219791304838934936387279630515658887485539659961265009321421059720176716708947162824378626801571847650024091762061008172625571327893613638956683252812460872115308998220696100462293803622250781016906532481844303936075489212041575353921582380137171487898138857279657975557703960397669255944572586836026330351201015911407019810196881844728252349871706989352500746246739934128633728161609865084795375265234146710503588616865119751368455059611417010662656542444610089402595766154466648593383612532447541139354746065164116466397617384545008417387953347319292748418523709382954073684016573202764322260104572053850324379711650017898301648724851941758431577684732732530974197468849025690865821258026893591314887586229321070660394639970413202824699842662167602380213079609311959732523089738843316936618119004887003333791949492468210799866238487789522341147699931943938995266536008571314911956415053855180789361316551568462200352674864453587775619457628440845266789022527127587740754838521372486723001413117245220232426753242675828177576859824828400218235780387636278112824686701}

ivanpubkey = {'e':6481764711916916397109273726155956377656536637642807312800757546468526438704587962838968130419349372877884749341748111210223731976275154922405947360547743L, 'n':338268226945045594040102034878758444764651534167506742110546096640083709576476389210311132469953959393591066992795836386110112598793559135339292833492240869157982347822379943074587320930881739344852033537843848473043128034075489712546721364258219630002902462839364391703058991174756678850745791050455715522819926432293598770270226759125320092184546422006399480232477970392705428953893948935507551291416633551949790971970309886077216112873834384725916279080756901772364218481535522170812626810368956042592229275686877306681530987143867223127594219058268997365351814588360451088611972783470143103530508782003784668721L}

andreaspubkey = {'e':2822540257849010647923776035626629838287235702704423096484847564654414465000881225428345657955502007283165026369457182106577477435673832705387872492044591, 'n':7882973334996053142664942135950444026685861344481859933376041911948219184913053557765978471764229745595651142694669215028934939643234703102261844806689829406623921142369711977840151829485724053715028017335204594765830956122106406342326605977659034321244220740521419889555563680752118278474604590311585813615909531550891420826960367366865035282430327062985682986212519631866305528935391849319049870616965616088088569190841921248106372804406270878233331052124845608476344647222603275832610760223847946462440120107424978654173015761966334681181665203909859876981557162746876336597081684996911168277402512063104549204937}

brentpubkey = {'e':13320637419729342324775464999050861486620207563289680221497576052388175183061457679807442479774032202586062376188244107037281567734856017246126615397816987, 'n':1664580811888919290322204386558991234618254900951529532302133070531168818003858721747272149690631987748580351955990179501255913110694396600216879077732002470881341935976316877085959939004416255719683229745084259916415734451722865966223832634066289733468156160367733425804203272891858242672578795220978282904336116171736295014176775641186644943132523508056618157857119718575880947188606341972480839706601198399600225860757160583497623882064668962077040113842430719849512995440241391131732067227002145871127232717089191139600707583888074613766713552503609290793641760419007328315145998064258640100176806286961432584093}

carterpubkey = {'e':7168437282876876633529422802762647606914193494803337768799081122185700696756563786082605549299608670375696543059776847908603899996329486965226631637840087, 'n':13724582806519489309968126783922147743627863615598200511401696263542228069378681666246810044371293214491884953122564270345036227213513705482186874644188248345092250636909105502001485885529938258392160401994355515499603431204210994869079065175753824307231699145470453865619794727786444147717765876934692580725863517337863828133103123656377281294656369539247378625499431358002787792903340479787368588244936134498455457634534658784891779316675575606443982304587254557775365931820487291639088098643507354164406035353826606748832467578180697619008125509252740195069184206787138540651467518667460180512988620825126472109931}

armonpubkey = {'e':3200941279173345080519384120021978738782253369732074792477284573335223989343368779528294503375136136053581878735944057988977016652466388720005919328614569, 'n':10553235881745543965137165331102432144225249224999120640550160795651004055141451077300441253063569456659555680900071806944299541573086873371906595419171669228793899400999760006896569579804445778200967916782666825777779527057870748694361762861470028374995168134276333298069549991573308145061643966828157536009984242670282950296031461069582089864549886939538988421709037403953460736874810775713352604046647570646063851167596096553164256127741778276907048527345789544310548454829925324855330039115251074424987130126399705652571956713617760718661078219136803706956075647543263871868993131570886861669612952313210350277323}

cosminpubkey = {'e':7464313175644513168887997744670197216333000296354197242445151519761504998981125780277221724878744115700245550050922885815874909770986351004470139292347799, 'n':5166923677011039755827733929519744979819679623762854241784562417614217033545741940486526418826236364419803842179010374289699995420620924879739633685352210702672742640627499819008012778100349108343082031728623289614040677248497446845750382415953993876705269331334135372972752054447786652022051356046844517168288974483920665154285041052294863296555313446636772615755907095066673797201543950176696075209934813375579921682346075069334926946959040236649186664203325185266985125536978403971085971814812113301555195462618654824626590790622973196762839114686728486351358141165471099773851900314642876491326191107813285382101}


kyungpubkey = {'e':11982834196181141260506010180308270855680653406337235774683333408763963018095300381624627449070255932606419233872822964155179661556140871823461403280265061, 'n':4545103278803184664785828362936668880385736545505423731656699929328390307650054478885855959293582492222118379534939515534504426410706682077004338092024910139743650930741139799450460528199982343120740446388950383095882206034545454151790038610951335439728039864518669360779845402779817426625909179794068292408331048258044602531678529469780131385941771393112498888925305762431363984275516442120381279894993082998112042145269189762889863936169922236763504067652051967137198111570516536122040089214964646207252038973487224346595800354866074385496633452068631506635900294186068046269028804783935234012560912143370854322011}

whitakerpubkey = {'e':1961187819685826468365136779361692346284587319331170293797380442981711617052308358785203431127570034065478147088934943463504711898262097524710828946161929, 'n':5220293180652733270755195484226554988025957180778111866066531921260742053227801887841799731238572363475563706429032069323733445905052162879700839788537681319527397161356564397513804886042808468789436053039403215219041923053291426259405050905986802204966674722504970715331195215999254156993121499173593576418062543281322433283314241631704243904535533349039349032764359013163901608903107127348380201430241401136948069753215772834135010946945297247718693460186633531322404614755849024748336571200652493116219224902877591567848820303000577863944677062535006436111211392380849014361509763074709175343781192906882800807463}


# This is the public key of the person who will control most of the resources.
controllerpubkey = {'e': 1515278400394037168869631887206225761783197636247636149274740854708478416229147500580877416652289990968676310353790883501744269103521055894342395180721167L, 'n': 8811850224687278929671477591179591903829730117649785862652866020803862826558480006479605958786097112503418194852731900367494958963787480076175614578652735061071079458992502737148356289391380249696938882025028801032667062564713111819847043202173425187133883586347323838509679062142786013585264788548556099117804213139295498187634341184917970175566549405203725955179602584979965820196023950630399933075080549044334508921319264315718790337460536601263126663173385674250739895046814277313031265034275415434440823182691254039184953842629364697394327806074576199279943114384828602178957150547925812518281418481896604655037L}



offcutresourcedata ="""# BUG: How do we come up with these values dynamically?
resource cpu .002
resource memory 1000000   # 1 MiB
resource diskused 100000 # .1 MiB
resource events 2
resource filewrite 1000
resource fileread 1000 
resource filesopened 1 
resource insockets 0
resource outsockets 0
resource netsend 0
resource netrecv 0
resource loopsend 0  # would change with prompt functionality (?)
resource looprecv 0
resource lograte 100 # the monitor might log something
resource random 0    # Shouldn't generate random numbers on our own
"""

bigresourcedata = """resource cpu .08
resource memory 100000000   # 100 MiB
resource diskused 80000000 # 80 MiB
resource events 50
resource filewrite 100000
resource fileread 100000
resource filesopened 10
resource insockets 10
resource outsockets 10
resource netsend 100000
resource netrecv 100000
resource loopsend 1000000
resource looprecv 1000000
resource lograte 30000
resource random 100
resource messport 11111
resource messport 12222
resource messport 13333
resource messport 14444
resource messport 15555
resource messport 16666
resource messport 17777
resource messport 18888
resource messport 19999
resource connport 11111
resource connport 12222
resource connport 13333
resource connport 14444
resource connport 15555
resource connport 16666
resource connport 17777
resource connport 18888
resource connport 19999

call gethostbyname_ex allow
call sendmess allow
call recvmess allow
call openconn allow
call waitforconn allow
call stopcomm allow                     # it doesn't make sense to restrict
call socket.close allow                 # let's not restrict
call socket.send allow                  # let's not restrict
call socket.recv allow                  # let's not restrict

# open and file.__init__ both have built in restrictions...
call open allow                         # can read / write
call file.__init__ allow                # can read / write
call file.close allow                   # shouldn't restrict
call file.flush allow                   # they are free to use
call file.next allow                    # free to use as well...
call file.read allow                    # allow read
call file.readline allow                # shouldn't restrict
call file.readlines allow               # shouldn't restrict
call file.seek allow                    # seek doesn't restrict
call file.write allow                   # shouldn't restrict (open restricts)
call file.writelines allow              # shouldn't restrict (open restricts)
call sleep allow                        # harmless
call settimer allow                     # we can't really do anything smart
call canceltimer allow                  # should be okay
call exitall allow                      # should be harmless 

call log.write allow
call log.writelines allow
call getmyip allow                      # They can get the external IP address
call listdir allow                      # They can list the files they created
call removefile allow                   # They can remove the files they create
call randomfloat allow                  # can get random numbers
call getruntime allow                   # can get the elapsed time
call getlock allow                      # can get a mutex
"""

smallresourcedata = """resource cpu .02
resource memory 30000000   # 30 MiB
resource diskused 20000000 # 20 MiB
resource events 15
resource filewrite 100000
resource fileread 100000
resource filesopened 5
resource insockets 5
resource outsockets 5
resource netsend 10000
resource netrecv 10000
resource loopsend 1000000
resource looprecv 1000000
resource lograte 30000
resource random 100
resource messport %s
resource messport %s
resource messport %s
resource messport %s
resource connport %s
resource connport %s
resource connport %s
resource connport %s

call gethostbyname_ex allow
call sendmess allow
call recvmess allow
call openconn allow
call waitforconn allow
call stopcomm allow                     # it doesn't make sense to restrict
call socket.close allow                 # let's not restrict
call socket.send allow                  # let's not restrict
call socket.recv allow                  # let's not restrict

# open and file.__init__ both have built in restrictions...
call open allow                         # can read / write
call file.__init__ allow                # can read / write
call file.close allow                   # shouldn't restrict
call file.flush allow                   # they are free to use
call file.next allow                    # free to use as well...
call file.read allow                    # allow read
call file.readline allow                # shouldn't restrict
call file.readlines allow               # shouldn't restrict
call file.seek allow                    # seek doesn't restrict
call file.write allow                   # shouldn't restrict (open restricts)
call file.writelines allow              # shouldn't restrict (open restricts)
call sleep allow                        # harmless
call settimer allow                     # we can't really do anything smart
call canceltimer allow                  # should be okay
call exitall allow                      # should be harmless 

call log.write allow
call log.writelines allow
call getmyip allow                      # They can get the external IP address
call listdir allow                      # They can list the files they created
call removefile allow                   # They can remove the files they create
call randomfloat allow                  # can get random numbers
call getruntime allow                   # can get the elapsed time
call getlock allow                      # can get a mutex
"""





def make_vessel(vesselname, pubkey, resourcetemplate, resourceargs):
  retdict = {'userkeys':[], 'ownerkey':pubkey, 'oldmetadata':None, 'stopfilename':vesselname+'.stop', 'logfilename':vesselname+'.log', 'statusfilename':vesselname+'.status', 'resourcefilename':'resource.'+vesselname, 'advertise':True, 'ownerinformation':'', 'status':'Fresh'}

  try:
    WindowsError

  except NameError: # not on windows...
    # make the vessel dirs...
    try:
      os.mkdir(vesselname)
    except OSError,e:
      if e[0] == 17:
        # directory exists
        pass
      else:
        raise

  else: # on Windows...

    # make the vessel dirs...
    try:
      os.mkdir(vesselname)
    except (OSError,WindowsError),e:
      if e[0] == 17 or e[0] == 183:
        # directory exists
        pass
      else:
        raise


  #### write the vessel's resource file...
  outfo = open(retdict['resourcefilename'],"w")
  # write the args into the resource data template
  outfo.write(resourcetemplate % resourceargs)
  outfo.close()
  
  return retdict



# lots of little things need to be initialized...   
def initialize_state():

  # initialize my configuration file.   This involves a few variables:
  #    pollfrequency --  the amount of time to sleep after a check when "busy
  #                      waiting".   This trades CPU load for responsiveness.
  #    ports         --  the ports the node manager could listen on.
  #    publickey     --  the public key used to identify the node...
  #    privatekey    --  the corresponding private key for the node...
  configuration = {}

  configuration['pollfrequency'] = 1.0

  # NOTE: I chose these randomly (they will be uniform across all NMs)...   
  # Was this wise?
  configuration['ports'] = [1224, 2888, 9625, 10348, 39303, 48126, 52862, 57344, 64310]

  print "Generating key..."
  keys = rsa_gen_pubpriv_keys(100)
  configuration['publickey'] = keys[0]
  configuration['privatekey'] = keys[1]


  print "Writing config file..."
  # write the config file...
  persist.commit_object(configuration,"nodeman.cfg")

  # write the offcut file...
  outfo = open("resources.offcut","w")
  outfo.write(offcutresourcedata)
  outfo.close()

#  vessel1 = make_vessel('v1',controllerpubkey,bigresourcedata, []) 
  vessel1 = make_vessel('v1',controllerpubkey,smallresourcedata, ('12345','12346', '12347','12348','12345','12346','12347','12348')) 
  vessel2 = make_vessel('v2',justinpubkey,smallresourcedata, ('20000','20001', '20002','20003','20000','20001','20002','20003')) 
  vessel3 = make_vessel('v3',ivanpubkey,smallresourcedata, ('30000','30001', '30002','30003','30000','30001','30002','30003')) 
  vessel4 = make_vessel('v4',andreaspubkey,smallresourcedata, ('21000','21001', '21002','21003','21000','21001','21002','21003')) 
  vessel5 = make_vessel('v5',brentpubkey,smallresourcedata, ('22000','22001', '22002','22003','22000','22001','22002','22003')) 
  vessel6 = make_vessel('v6',carterpubkey,smallresourcedata, ('23000','23001', '23002','23003','23000','23001','23002','23003')) 
  vessel7 = make_vessel('v7',armonpubkey,smallresourcedata, ('24000','24001', '24002','24003','24000','24001','24002','24003')) 
  vessel8 = make_vessel('v8',cosminpubkey,smallresourcedata, ('25000','25001', '25002','25003','25000','25001','25002','25003')) 
  vessel9 = make_vessel('v9',kyungpubkey,smallresourcedata, ('26000','26001', '26002','26003','26000','26001','26002','26003')) 
  vessel10 = make_vessel('v10',whitakerpubkey,smallresourcedata, ('27000','27001', '27002','27003','27000','27001','27002','27003')) 
  

  vesseldict = {'v1':vessel1, 'v2':vessel2, 'v3':vessel3, 'v4':vessel4, 'v5':vessel5, 'v6':vessel6, 'v7':vessel7, 'v8':vessel8, 'v9':vessel9, 'v10':vessel10}

  print "Writing vessel dictionary..."
  # write out the vessel dictionary...
  persist.commit_object(vesseldict,"vesseldict")










if __name__ == '__main__':
  initialize_state() 
