# simple keypair creator...
import sys
import random

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



if len(sys.argv) != 4:
  print "usage %s: username keylen dir"%(sys.argv[0])
  sys.exit(0)

#end include rsa.repy

# need to support random number generation
randomfloat = random.random

pubfn = sys.argv[3]+sys.argv[1]+'.publickey'
privfn = sys.argv[3]+sys.argv[1]+'.privatekey'
keylength = int(sys.argv[2])

print "Generating key files called '"+pubfn+"' and '"+privfn+"' of length "+str(keylength)+"."
print "This may take a moment..."

keys = rsa_gen_pubpriv_keys(keylength)

rsa_publickey_to_file(keys[0],pubfn)
rsa_privatekey_to_file(keys[1],privfn)

print "Success!"
