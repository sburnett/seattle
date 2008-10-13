""" 
Author: Justin Cappos

Module: Node Manager request handler.   This securely handles a request from a 
        client.   It does not worry about how it gets the connection, 
        concurrency, etc.   It does worry about slow retrieval attacks, etc.

Start date: August 28th, 2008

The design goals of this version are to be secure, simple, and reliable (in 
that order).   

I think this is fairly straightforward...   Get requests, check them, and
pass them to the appropriate API function
"""

  

# repy signeddata to protect request information
#begin include signeddata.repy
""" Justin Cappos -- routines that create and verify signatures and prevent
replay / freeze / out of sequence / misdelivery attacks

Replay attack:   When someone provides information you signed before to try
to get you to perform an old action again.   For example, A sends messages to
the node manager to provide a vessel to B (B intercepts this traffic).   Later 
A acquires the vessel again.   B should not be able to replay the messages A 
sent to the node manager to have the vessel transferred to B again.

Freeze attack:   When an attacker can act as a man-in-the-middle and provide
stale information to an attacker.   For example, B can intercept all traffic
between the node manager and A.   If C makes a change on the node manager, then
B should not be able to prevent A from seeing the change (at least within 
some time bound).

Out of sequence attack:   When someone can skip sending some messages but
deliver others.   For example, A wants to stop the current program, upload
a new copy of the program, and start the program again.   It should be possible
for A to specify that these actions must be performed in order and without 
skipping any of the prior actions (regardless of failures, etc.).

Misdelivery attack:   Messages should only be acted upon by the nodes that 
the user intended.   A malicious party should not be able to "misdeliver" a
message and have a different node perform the action.



I have support for "sequence numbers" which will require that intermediate 
events are not skipped.    The sequence numbers are a tuple: (tag, version)

"""


#begin include sha.repy
#!/usr/bin/env python
# -*- coding: iso-8859-1

"""A sample implementation of SHA-1 in pure Python.

   Adapted by Justin Cappos from the version at: http://codespeak.net/pypy/dist/pypy/lib/sha.py

   Framework adapted from Dinu Gherman's MD5 implementation by
   J. Hall`en and L. Creighton. SHA-1 implementation based directly on
   the text of the NIST standard FIPS PUB 180-1.

date    = '2004-11-17'
version = 0.91 # Modernised by J. Hall`en and L. Creighton for Pypy
"""



# ======================================================================
# Bit-Manipulation helpers
#
#   _long2bytes() was contributed by Barry Warsaw
#   and is reused here with tiny modifications.
# ======================================================================

def _sha_long2bytesBigEndian(n, thisblocksize=0):
    """Convert a long integer to a byte string.

    If optional blocksize is given and greater than zero, pad the front
    of the byte string with binary zeros so that the length is a multiple
    of blocksize.
    """

    # Justin: I changed this to avoid using pack. I didn't test performance, etc
    s = ''
    while n > 0:
        #original: 
        # s = struct.pack('>I', n & 0xffffffffL) + s
        # n = n >> 32
        s = chr(n & 0xff) + s
        n = n >> 8

    # Strip off leading zeros.
    for i in range(len(s)):
        if s[i] <> '\000':
            break
    else:
        # Only happens when n == 0.
        s = '\000'
        i = 0

    s = s[i:]

    # Add back some pad bytes. This could be done more efficiently
    # w.r.t. the de-padding being done above, but sigh...
    if thisblocksize > 0 and len(s) % thisblocksize:
        s = (thisblocksize - len(s) % thisblocksize) * '\000' + s

    return s


def _sha_bytelist2longBigEndian(list):
    "Transform a list of characters into a list of longs."

    imax = len(list)/4
    hl = [0L] * imax

    j = 0
    i = 0
    while i < imax:
        b0 = long(ord(list[j])) << 24
        b1 = long(ord(list[j+1])) << 16
        b2 = long(ord(list[j+2])) << 8
        b3 = long(ord(list[j+3]))
        hl[i] = b0 | b1 | b2 | b3
        i = i+1
        j = j+4

    return hl


def _sha_rotateLeft(x, n):
    "Rotate x (32 bit) left n bits circularly."

    return (x << n) | (x >> (32-n))


# ======================================================================
# The SHA transformation functions
#
# ======================================================================

# Constants to be used
sha_K = [
    0x5A827999L, # ( 0 <= t <= 19)
    0x6ED9EBA1L, # (20 <= t <= 39)
    0x8F1BBCDCL, # (40 <= t <= 59)
    0xCA62C1D6L  # (60 <= t <= 79)
    ]

class sha:
    "An implementation of the MD5 hash function in pure Python."

    def __init__(self):
        "Initialisation."
        
        # Initial message length in bits(!).
        self.length = 0L
        self.count = [0, 0]

        # Initial empty message as a sequence of bytes (8 bit characters).
        self.inputdata = []

        # Call a separate init function, that can be used repeatedly
        # to start from scratch on the same object.
        self.init()


    def init(self):
        "Initialize the message-digest and set all fields to zero."

        self.length = 0L
        self.inputdata = []

        # Initial 160 bit message digest (5 times 32 bit).
        self.H0 = 0x67452301L
        self.H1 = 0xEFCDAB89L
        self.H2 = 0x98BADCFEL
        self.H3 = 0x10325476L
        self.H4 = 0xC3D2E1F0L

    def _transform(self, W):

        for t in range(16, 80):
            W.append(_sha_rotateLeft(
                W[t-3] ^ W[t-8] ^ W[t-14] ^ W[t-16], 1) & 0xffffffffL)

        A = self.H0
        B = self.H1
        C = self.H2
        D = self.H3
        E = self.H4

        """
        This loop was unrolled to gain about 10% in speed
        for t in range(0, 80):
            TEMP = _sha_rotateLeft(A, 5) + sha_f[t/20] + E + W[t] + sha_K[t/20]
            E = D
            D = C
            C = _sha_rotateLeft(B, 30) & 0xffffffffL
            B = A
            A = TEMP & 0xffffffffL
        """

        for t in range(0, 20):
            TEMP = _sha_rotateLeft(A, 5) + ((B & C) | ((~ B) & D)) + E + W[t] + sha_K[0]
            E = D
            D = C
            C = _sha_rotateLeft(B, 30) & 0xffffffffL
            B = A
            A = TEMP & 0xffffffffL

        for t in range(20, 40):
            TEMP = _sha_rotateLeft(A, 5) + (B ^ C ^ D) + E + W[t] + sha_K[1]
            E = D
            D = C
            C = _sha_rotateLeft(B, 30) & 0xffffffffL
            B = A
            A = TEMP & 0xffffffffL

        for t in range(40, 60):
            TEMP = _sha_rotateLeft(A, 5) + ((B & C) | (B & D) | (C & D)) + E + W[t] + sha_K[2]
            E = D
            D = C
            C = _sha_rotateLeft(B, 30) & 0xffffffffL
            B = A
            A = TEMP & 0xffffffffL

        for t in range(60, 80):
            TEMP = _sha_rotateLeft(A, 5) + (B ^ C ^ D)  + E + W[t] + sha_K[3]
            E = D
            D = C
            C = _sha_rotateLeft(B, 30) & 0xffffffffL
            B = A
            A = TEMP & 0xffffffffL


        self.H0 = (self.H0 + A) & 0xffffffffL
        self.H1 = (self.H1 + B) & 0xffffffffL
        self.H2 = (self.H2 + C) & 0xffffffffL
        self.H3 = (self.H3 + D) & 0xffffffffL
        self.H4 = (self.H4 + E) & 0xffffffffL
    

    # Down from here all methods follow the Python Standard Library
    # API of the sha module.

    def update(self, inBuf):
        """Add to the current message.

        Update the md5 object with the string arg. Repeated calls
        are equivalent to a single call with the concatenation of all
        the arguments, i.e. m.update(a); m.update(b) is equivalent
        to m.update(a+b).

        The hash is immediately calculated for all full blocks. The final
        calculation is made in digest(). It will calculate 1-2 blocks,
        depending on how much padding we have to add. This allows us to
        keep an intermediate value for the hash, so that we only need to
        make minimal recalculation if we call update() to add more data
        to the hashed string.
        """

        leninBuf = long(len(inBuf))

        # Compute number of bytes mod 64.
        index = (self.count[1] >> 3) & 0x3FL

        # Update number of bits.
        self.count[1] = self.count[1] + (leninBuf << 3)
        if self.count[1] < (leninBuf << 3):
            self.count[0] = self.count[0] + 1
        self.count[0] = self.count[0] + (leninBuf >> 29)

        partLen = 64 - index

        if leninBuf >= partLen:
            self.inputdata[index:] = list(inBuf[:partLen])
            self._transform(_sha_bytelist2longBigEndian(self.inputdata))
            i = partLen
            while i + 63 < leninBuf:
                self._transform(_sha_bytelist2longBigEndian(list(inBuf[i:i+64])))
                i = i + 64
            else:
                self.inputdata = list(inBuf[i:leninBuf])
        else:
            i = 0
            self.inputdata = self.inputdata + list(inBuf)


    def digest(self):
        """Terminate the message-digest computation and return digest.

        Return the digest of the strings passed to the update()
        method so far. This is a 16-byte string which may contain
        non-ASCII characters, including null bytes.
        """

        H0 = self.H0
        H1 = self.H1
        H2 = self.H2
        H3 = self.H3
        H4 = self.H4
        inputdata = [] + self.inputdata
        count = [] + self.count

        index = (self.count[1] >> 3) & 0x3fL

        if index < 56:
            padLen = 56 - index
        else:
            padLen = 120 - index

        padding = ['\200'] + ['\000'] * 63
        self.update(padding[:padLen])

        # Append length (before padding).
        bits = _sha_bytelist2longBigEndian(self.inputdata[:56]) + count

        self._transform(bits)

        # Store state in digest.
        digest = _sha_long2bytesBigEndian(self.H0, 4) + \
                 _sha_long2bytesBigEndian(self.H1, 4) + \
                 _sha_long2bytesBigEndian(self.H2, 4) + \
                 _sha_long2bytesBigEndian(self.H3, 4) + \
                 _sha_long2bytesBigEndian(self.H4, 4)

        self.H0 = H0 
        self.H1 = H1 
        self.H2 = H2
        self.H3 = H3
        self.H4 = H4
        self.inputdata = inputdata 
        self.count = count 

        return digest


    def hexdigest(self):
        """Terminate and return digest in HEX form.

        Like digest() except the digest is returned as a string of
        length 32, containing only hexadecimal digits. This may be
        used to exchange the value safely in email or other non-
        binary environments.
        """
        return ''.join(['%02x' % ord(c) for c in self.digest()])

    def copy(self):
        """Return a clone object. (not implemented)

        Return a copy ('clone') of the md5 object. This can be used
        to efficiently compute the digests of strings that share
        a common initial substring.
        """
        raise Exception, "not implemented"


# ======================================================================
# Mimic Python top-level functions from standard library API
# for consistency with the md5 module of the standard library.
# ======================================================================

# These are mandatory variables in the module. They have constant values
# in the SHA standard.

sha_digest_size = sha_digestsize = 20
sha_blocksize = 1

def sha_new(arg=None):
    """Return a new sha crypto object.

    If arg is present, the method call update(arg) is made.
    """

    crypto = sha()
    if arg:
        crypto.update(arg)

    return crypto


# gives the hash of a string
def sha_hash(string):
    crypto = sha()
    crypto.update(string)
    return crypto.digest()


# gives the hash of a string
def sha_hexhash(string):
    crypto = sha()
    crypto.update(string)
    return crypto.hexdigest()
#end include sha.repy
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
#begin include time.repy
"""
   Author: Justin Cappos

   Start Date: 8 August 2008

   Description:

   This module handles getting the time from an external source.   We get the
   remote time once and then use the offset from the local clock from then on.
"""


# Use for random sampling...
#begin include random.repy
#already included random.repy
#end include random.repy


class TimeError(Exception):
  pass


time_query_times = []

# See RFC 2030 (http://www.ietf.org/rfc/rfc2030.txt) for details about NTP

# this unpacks the data from the packet and changes it to a float
def time_convert_timestamp_to_float(timestamp):
  integerpart = (ord(timestamp[0])<<24) + (ord(timestamp[1])<<16) + (ord(timestamp[2])<<8) + (ord(timestamp[3]))
  floatpart = (ord(timestamp[4])<<24) + (ord(timestamp[5])<<16) + (ord(timestamp[6])<<8) + (ord(timestamp[7]))
  return integerpart + floatpart / float(2**32)

def time_decode_NTP_packet(ip, port, mess, ch):
  time_settime(time_convert_timestamp_to_float(mess[40:48]))
  stopcomm(ch)


# sets a remote time as the current time
#BUG: Do I need to compensate for the time taken to contact the time server
def time_settime(currenttime):
  time_query_times.append((getruntime(), currenttime))


def time_updatetime(localport):
  try:
    ip = getmyip()
  except Exception, e:
    raise TimeError, str(e)

  timeservers = ["time-a.nist.gov", "time-b.nist.gov", "time-a.timefreq.bldrdoc.gov", "time-b.timefreq.bldrdoc.gov", "time-c.timefreq.bldrdoc.gov", "utcnist.colorado.edu", "time.nist.gov", "time-nw.nist.gov", "nist1.symmetricom.com", "nist1-dc.WiTime.net", "nist1-ny.WiTime.net", "nist1-sj.WiTime.net", "nist1.aol-ca.symmetricom.com", "nist1.aol-va.symmetricom.com", "nist1.columbiacountyga.gov", "nist.expertsmi.com", "nist.netservicesgroup.com"]

  startlen = len(time_query_times)
  listenhandle = recvmess(ip,localport, time_decode_NTP_packet)

  # always close the handle before returning...
  try: 
    # try five random servers times...
    for servername in random_sample(timeservers,5):

      # this sends a request, version 3 in "client mode"
      ntp_request_string = chr(27)+chr(0)*47
      try: 
        sendmess(servername,123, ntp_request_string, ip, localport) # 123 is the NTP port
      except Exception:
        # most likely a lookup error...
        continue

      # wait for 5 seconds for a response before retrying
      for junkiterations in range(10):
        sleep(.5)

        if startlen < len(time_query_times):
          # If we've had a response, we're done!
          return
    
    
  finally:
    stopcomm(listenhandle)

  # Failure, tried servers without luck...
  raise TimeError, "Time Server update failed.  Perhaps retry later..."


def time_gettime():
  if time_query_times == []:
    raise TimeError

  # otherwise use the most recent data...
  latest_update = time_query_times[-1]

  # first item is the getruntime(), second is NTP time...
  elapsedtimesinceupdate = getruntime() - latest_update[0]

  return latest_update[1] + elapsedtimesinceupdate

# in case you want to change to time since the 1970 (as is common)
time_seconds_from_1900_to_1970 = 2208988800

#end include time.repy


# The signature for a piece of data is appended to the end and has the format:
# \n!publickey!timestamp!expirationtime!sequencedata!destination!signature
# The signature is actually the sha hash of the data (including the
# publickey, timestamp, expirationtime, sequencedata and destination) encrypted
# by the private key.



# I'll allow None and any int, long, or float (can be 0 or negative)
def signeddata_is_valid_timestamp(timestamp):
  if timestamp == None:
    return True

  if type(timestamp) is not int and type(timestamp) is not long and type(timestamp) is not float:
    return False

  return True

  
# I'll allow None and any int, long, or float that is 0 or positive
def signeddata_is_valid_expirationtime(expirationtime):
  if expirationtime == None:
    return True

  if type(expirationtime) is not int and type(expirationtime) is not long and type(expirationtime) is not float:
    return False

  if expirationtime < 0:
    return False

  return True





# sequence numbers must be 'tag:num' where tag doesn't contain ':','\n', or '!' # and num is a number
def signeddata_is_valid_sequencenumber(sequencenumber):
  if sequencenumber == None:
    return True

  if type(sequencenumber) != tuple:
    return False

  if len(sequencenumber) != 2:
    return False

  if type(sequencenumber[0]) != str:
    return False
  
  if '!' in sequencenumber[0] or ':' in sequencenumber[0] or '\n' in sequencenumber[0]:
    return False

  if type(sequencenumber[1]) != long and type(sequencenumber[1]) != int:
    return False

  return True

# Destination is an "opaque string" or None.  Should not contain a '!' or '\n'
def signeddata_is_valid_destination(destination):
  if type(destination) == type(None):
    return True

  # a string without '!' or '\n' ('!' is the separator character, '\n' is not
  # allowed anywhere in the signature)
  if type(destination) == type('abc') and '!' not in destination and '\n' not in destination:
    return True

  return False
  



def signeddata_signdata(data, privatekey, publickey, timestamp=None, expiration=None, sequenceno=None,destination=None):

# NOTE: This takes waaaay too long.   I'm going to do something simpler...
#  if not rsa_is_valid_privatekey(privatekey):
#    raise ValueError, "Invalid Private Key"
  if not privatekey:
    raise ValueError, "Invalid Private Key"
    

  if not rsa_is_valid_publickey(publickey):
    raise ValueError, "Invalid Public Key"

  if not signeddata_is_valid_timestamp(timestamp):
    raise ValueError, "Invalid Timestamp"

  if not signeddata_is_valid_expirationtime(expiration):
    raise ValueError, "Invalid Expiration Time"

  if not signeddata_is_valid_sequencenumber(sequenceno):
    raise ValueError, "Invalid Sequence Number"

  if not signeddata_is_valid_destination(destination):
    raise ValueError, "Invalid Destination"


  # Build up \n!pubkey!timestamp!expire!sequence!dest!signature
  totaldata = data + "\n!"+rsa_publickey_to_string(publickey)
  totaldata = totaldata+"!"+signeddata_timestamp_to_string(timestamp)
  totaldata = totaldata+"!"+signeddata_expiration_to_string(expiration)
  totaldata = totaldata+"!"+signeddata_sequencenumber_to_string(sequenceno)
  totaldata = totaldata+"!"+signeddata_destination_to_string(destination)
  
  # Time to get the hash...
  shahashobj = sha()
  shahashobj.update(totaldata)
  hashdata = shahashobj.digest()


  # ...and sign it
  signature = rsa_sign(hashdata, privatekey)

  totaldata = totaldata+"!"+str(signature)

  return totaldata


# return [original data, signature]
def signeddata_split_signature(data):
  return data.rsplit('\n',1)


# checks the signature.   If the public key is specified it must match that in
# the file...
def signeddata_issignedcorrectly(data, publickey=None):
  # I'll check signature over all of thesigneddata
  thesigneddata, signature = data.rsplit('!',1)
  junk, rawpublickey, junktimestamp, junkexpiration, junksequenceno, junkdestination = thesigneddata.rsplit('!',5)
  
  if publickey != None and rsa_string_to_publickey(rawpublickey) != publickey:
    return False

  publickey = rsa_string_to_publickey(rawpublickey)

  # extract the hash from the signature
  signedhash = rsa_verify(signature, publickey)

  # Does the hash match the signed data?
  if signedhash == sha_hash(thesigneddata):
    return True
  else:
    return False
  

def signeddata_string_to_destination(destination):
  if destination == 'None':
    return None
  return destination

def signeddata_destination_to_string(destination):
  return str(destination)


def signeddata_string_to_timestamp(rawtimestamp):
  if rawtimestamp == 'None':
    return None
  return float(rawtimestamp)


def signeddata_timestamp_to_string(timestamp):
  return str(timestamp)

def signeddata_string_to_expiration(rawexpiration):
  if rawexpiration == 'None':
    return None
  return float(rawexpiration)

def signeddata_expiration_to_string(expiration):
  return str(expiration)



def signeddata_string_to_sequencenumber(sequencenumberstr):
  if sequencenumberstr == 'None' or sequencenumberstr == None:
    return None

  if type(sequencenumberstr) is not str:
    raise ValueError, "Invalid sequence number type '"+str(type(sequencenumberstr))+"' (must be string)"
    
  if len(sequencenumberstr.split(':')) != 2:
    raise ValueError, "Invalid sequence number string (does not contain 1 ':')"

  if '!' in sequencenumberstr:
    raise ValueError, "Invalid sequence number data: '!' not allowed"
  
  return sequencenumberstr.split(':')[0],int(sequencenumberstr.split(':')[1])


def signeddata_sequencenumber_to_string(sequencenumber):
  if type(sequencenumber) is type(None):
    return 'None'

  if type(sequencenumber[0]) is not str:
    raise ValueError, "Invalid sequence number type"

  if type(sequencenumber[1]) is not long and type(sequencenumber[1]) is not int:
    raise ValueError, "Invalid sequence number count type"
    
  if len(sequencenumber) != 2:
    raise ValueError, "Invalid sequence number"

  return sequencenumber[0]+":"+str(sequencenumber[1])


def signeddata_iscurrent(expiretime):
  if expiretime == None:
    return True

  # may throw TimeError...
  currenttime = time_gettime()
  if expiretime > currenttime:
    return True
  else:
    return False




def signeddata_has_good_sequence_transition(oldsequence, newsequence):
  # None is always allowed by any prior sequence
  if newsequence == None:
    return True

  if oldsequence == None: 
    # is this the start of a sequence when there was none prior?
    if newsequence[1] == 0:
      return True
    return False

  # They are from the same sequence
  if oldsequence[0] == newsequence[0]:
    # and this must be the next number to be valid
    if oldsequence[1] + 1 == newsequence[1]:
      return True
    return False

  else: 
    # Different sequences
 
    # is this the start of a new sequence?
    if newsequence[1] == 0:
      return True

    # otherwise this isn't good
    return False


# used in lieu of a global for destination checking
signeddata_identity = {}

# Used to set identity for destination checking...
def signeddata_set_identity(identity):
  signeddata_identity['me'] = identity


def signeddata_destined_for_me(destination):
  # None means it's for everyone
  if destination == None:
    return True

  # My identity wasn't set and the destination was, so fail...
  if 'me' not in signeddata_identity:
    return False

  # otherwise, am I in the colon delimited list?
  if signeddata_identity['me'] in destination.split(':'):
    return True
  return False



def signeddata_split(data):
  originaldata, rawpublickey, rawtimestamp, rawexpiration, rawsequenceno,rawdestination, junksignature = data.rsplit('!',6)
  
  # strip the '\n' off of the original data...
  return originaldata[:-1], rsa_string_to_publickey(rawpublickey), signeddata_string_to_timestamp(rawtimestamp), signeddata_string_to_expiration(rawexpiration), signeddata_string_to_sequencenumber(rawsequenceno), signeddata_string_to_destination(rawdestination)



def signeddata_getcomments(signeddata, publickey=None):
  """Returns a list of problems with the signed data (but doesn't look at sequence number or timestamp data)."""
  returned_comments = []

  try:
    junkdata, pubkey, timestamp, expiretime, sequenceno, destination = signeddata_split(signeddata)
  except KeyError:
    return ['Malformed signed data']

  if publickey != None and publickey != pubkey:
    returned_comments.append('Different public key')

  if not signeddata_issignedcorrectly(signeddata, publickey):
    returned_comments.append("Bad signature")
  
  try:
    if not signeddata_iscurrent(expiretime):
      returned_comments.append("Expired signature")
  except TimeError:
    returned_comments.append("Cannot check expiration")

  if destination != None and not signeddata_destined_for_me(destination):
    returned_comments.append("Not destined for this node")

  return returned_comments



signeddata_warning_comments = [ 'Timestamps match', "Cannot check expiration" ]
signeddata_fatal_comments = ['Malformed signed data', 'Different public key', "Bad signature", "Expired signature", 'Public keys do not match', 'Invalid sequence transition', 'Timestamps out of order', 'Not destined for this node']

signeddata_all_comments = signeddata_warning_comments + signeddata_fatal_comments


def signeddata_shouldtrust(oldsigneddata, newsigneddata, publickey=None):
  """ Returns False for 'don't trust', None for 'use your discretion' and True 
  for everything is okay.   The second item in the return value is a list of
  reasons / justifications"""

  returned_comments = []

# we likely only want to keep the signature data around in many cases.   For 
# example, if the request is huge.   
#  if not signeddata_issignedcorrectly(oldsigneddata, publickey):
#    raise ValueError, "Old signed data is not correctly signed!"

  if not signeddata_issignedcorrectly(newsigneddata, publickey):
    returned_comments.append("Bad signature")
    return False, returned_comments
    
  # extract information about the signatures
  oldjunk, oldpubkey, oldtime, oldexpire, oldsequence, olddestination = signeddata_split(oldsigneddata)
  newjunk, newpubkey, newtime, newexpire, newsequence, newdestination = signeddata_split(newsigneddata)
    
  if oldpubkey != newpubkey:
    returned_comments.append('Public keys do not match')
    # fall through and reject below

  # get comments on everything but the timestamp and sequence number
  returned_comments = returned_comments + signeddata_getcomments(newsigneddata, publickey)
  
  # check the sequence number data...
  if not signeddata_has_good_sequence_transition(oldsequence, newsequence):
    returned_comments.append('Invalid sequence transition')

  # check the timestamps...  
  if (newtime == None and oldtime != None) or oldtime == None or oldtime > newtime:
    # if the timestamps are reversed (None is the earliest possible)
    returned_comments.append('Timestamps out of order')
  elif oldtime != None and newtime != None and oldtime == newtime:
    # the timestamps are equal but not none...
    returned_comments.append('Timestamps match')
  else:   # So they either must both be None or oldtime < newtime
    assert((newtime == oldtime == None) or oldtime < newtime)
  

  # let's see what happened...
  if returned_comments == []:
    return True, []
  for comment in returned_comments:
    if comment in signeddata_fatal_comments:
      return False, returned_comments

    # if not a failure, should be a warning comment
    assert(comment in signeddata_warning_comments)

  # Warnings, so I won't return True
  return None, returned_comments
  
#end include signeddata.repy

# get requests (encapsulated in session messages)
#begin include session.repy
# This module wraps communications in a signaling protocol.   The purpose is to
# overlay a connection-based protocol with explicit message signaling.   
#
# The protocol is to send the size of the message followed by \n and then the
# message itself.   The size of a message must be able to be stored in 
# sessionmaxdigits.   A size of -1 indicates that this side of the connection
# should be considered closed.
#
# Note that the client will block while sending a message, and the receiver 
# will block while recieving a message.   
#
# While it should be possible to reuse the connectionbased socket for other 
# tasks so long as it does not overlap with the time periods when messages are 
# being sent, this is inadvisable.

class SessionEOF(Exception):
  pass

sessionmaxdigits = 20

# get the next message off of the socket...
def session_recvmessage(socketobj):

  messagesizestring = ''
  # first, read the number of characters...
  for junkcount in range(sessionmaxdigits):
    currentbyte = socketobj.recv(1)

    if currentbyte == '\n':
      break
    
    # not a valid digit
    if currentbyte not in '0123456789' and messagesizestring != '' and currentbyte != '-':
      raise ValueError, "Bad message size"
     
    messagesizestring = messagesizestring + currentbyte

  else:
    # too large
    raise ValueError, "Bad message size"

  messagesize = int(messagesizestring)
  
  # nothing to read...
  if messagesize == 0:
    return ''

  # end of messages
  if messagesize == -1:
    raise SessionEOF, "Connection Closed"

  if messagesize < 0:
    raise ValueError, "Bad message size"

  data = ''
  while len(data) < messagesize:
    chunk =  socketobj.recv(messagesize-len(data))
    if chunk == '': 
      raise SessionEOF, "Connection Closed"
    data = data + chunk

  return data

# a private helper function
def session_sendhelper(socketobj,data):
  sentlength = 0
  # if I'm still missing some, continue to send (I could have used sendall
  # instead but this isn't supported in repy currently)
  while sentlength < len(data):
    thissent = socketobj.send(data[sentlength:])
    sentlength = sentlength + thissent



# send the message 
def session_sendmessage(socketobj,data):
  header = str(len(data)) + '\n'
  session_sendhelper(socketobj,header)

  session_sendhelper(socketobj,data)



#end include session.repy

# the API for the node manager
import nmAPI

# for socket.error
import socket

# for logging informative errors
import traceback


def initialize(myip, publickey, version):
  
  # this allows requests to specify they should only be enacted by us (by 
  # public key which should be unique)
  signeddata_set_identity(str(publickey))

  # init the node manager's API (mostly for information it returns when a call
  # gets generic node information)

  # we return the node dict
  return nmAPI.initialize(myip, publickey, version)


  



# this takes a connection and safely processes the request.   
def handle_request(socketobj):


  try:
    # let's get the request...
    # BUG: Should prevent endless data / slow retrival attacks
    fullrequest = session_recvmessage(socketobj)
  except (socket.error, SessionEOF, ValueError), e:
    # close if possible
    try:
      socketobj.close()
    except:
      pass

    # I can't handle this, let's exit
    # BUG: REMOVE LOGGING IN PRODUCTION VERSION (?)
    print e
    return

  # handle the request as appropriate
  try:
    retstring = process_API_call(fullrequest)

  # Bad parameters, signatures, etc.
  except nmAPI.BadRequest,e:
    try:
      session_sendmessage(socketobj, str(e)+"\nError")
      socketobj.close()
    except:
      pass
    return

  # Other exceptions only should happen on an internal error
  except Exception,e:
    try:
      traceback.print_exc()
      session_sendmessage(socketobj,"Internal Error\nError")
      socketobj.close()
    except:
      pass
    return
 
  
  # send any output from the command
  try:
    session_sendmessage(socketobj,retstring)
    socketobj.close()
  except:
    pass





# I'm going to have a table that defines what to check for the calls.   
# The idea is to make the logic as clear as possible and punt the "decision 
# making" about what needs to be checked into the table.

# The format of a request is:
#    requesttype|arg1|arg2 ... 
# requests are protected using the signeddata mechanism, so a trailer contains
# the signature information

# Entries are key / values like requesttype: (numargs, whocanperform, function)
# request type is the string that identifies which request
# numargs is the number of args that the string must have
# whocanperform is either 'Public', 'User', 'Owner' and specifies the minimum
#               amount of privilege one must have to perform the action
# function is the function that should be called with the arguments

# NOTE: if whocanperform is 'User' or 'Owner' the first argument MUST be the
# vessel name...

# Calls that the node manager understands.   The key is the "call name"
# the value is a tuple with number of args, protection, and the actual function
API_dict = { \
  'GetVessels': (0, 'Public', nmAPI.getvessels), \
  'GetVesselResources': (1, 'Public', nmAPI.getvesselresources), \
  'GetOffcutResources': (0, 'Public', nmAPI.getoffcutresources), \
  'StartVessel': (2, 'User', nmAPI.startvessel), \
  'StopVessel': (1, 'User', nmAPI.stopvessel), \
  'AddFileToVessel': (3, 'User', nmAPI.addfiletovessel), \
  'RetrieveFileFromVessel': (2, 'User', nmAPI.retrievefilefromvessel), \
  'DeleteFileInVessel': (2, 'User', nmAPI.deletefileinvessel), \
  'ReadVesselLog': (1, 'User', nmAPI.readvessellog), \
  'ChangeOwner': (2, 'Owner', nmAPI.changeowner), \
  'ChangeUsers': (2, 'Owner', nmAPI.changeusers), \
  'ChangeOwnerInformation': (2, 'Owner', nmAPI.changeownerinformation), \
  'ChangeAdvertise': (2, 'Owner', nmAPI.changeadvertise), \
  'SplitVessel': (2, 'Owner', nmAPI.splitvessel), \
  'JoinVessels': (2, 'Owner', nmAPI.joinvessels), \
  'SetRestrictions': (2, 'Owner', nmAPI.setrestrictions) \
}


def process_API_call(fullrequest):

  callname = fullrequest.split('|')[0]

  if callname not in API_dict:
    raise nmAPI.BadRequest("Unknown Call")

  # find the entry that describes this call...
  numberofargs, permissiontype, APIfunction = API_dict[callname]
  
  # we'll do the signature checks first... (the signature needs to be stripped
  # off to get the args anyways)...

  if permissiontype == 'Public':
    # There should be no signature, so this is the raw request...
    if len(fullrequest.split('|')) < numberofargs-1:
      raise nmAPI.BadRequest("Not Enough Arguments")

    # If there are 3 args, we want to split at most 3 times (the first item is 
    # the callname)
    callargs = fullrequest.split('|',numberofargs)
    # return any output for the user...
    return APIfunction(*callargs[1:])

  else:
    # strip off the signature and get the requestdata
    requestdata = signeddata_split_signature(fullrequest)[0]

    # NOTE: the first argument *must* be the vessel name!!!!!!!!!!!
    vesselname = requestdata.split('|',2)[1]

    if vesselname not in nmAPI.vesseldict:
      raise nmAPI.BadRequest('Unknown Vessel')

    # I must have something to check...
    if permissiontype == 'Owner':
      # only the owner is allowed, so the list of keys is merely that key
      allowedkeys = [ nmAPI.vesseldict[vesselname]['ownerkey'] ]
    else:
      # the user keys are also allowed
      allowedkeys = [ nmAPI.vesseldict[vesselname]['ownerkey'] ] + nmAPI.vesseldict[vesselname]['userkeys']

    # I need to pass the fullrequest in here...
    ensure_is_correctly_signed(fullrequest, allowedkeys, nmAPI.vesseldict[vesselname]['oldmetadata'])
    
    # If there are 3 args, we want to split at most 3 times (the first item is 
    # the callname)
    callargs = requestdata.split('|',numberofargs)
    # return any output for the user...
    return APIfunction(*callargs[1:])






# Raise a BadRequest exception if it's not correctly signed...
def ensure_is_correctly_signed(fullrequest, allowedkeys, oldmetadata):

  # ensure it's correctly signed, if not report this and exit
  if not signeddata_issignedcorrectly(fullrequest):
    raise nmAPI.BadRequest,"Bad Signature on '"+fullrequest+"'"

  request, requestsignature = signeddata_split_signature(fullrequest)

  signingpublickey = signeddata_split(fullrequest)[1]

  # If they care about the key, do they have a valid key?
  if allowedkeys and signingpublickey not in allowedkeys:
    raise nmAPI.BadRequest('Insufficient Permissions')


  # No constraints!   We're done
  if not oldmetadata:
    return

  (shouldtrust, reasons) = signeddata_shouldtrust(oldmetadata, requestsignature)

  if not shouldtrust:
    # let's tell them what is wrong.
    raise nmAPI.BadRequest,"Signature problem: "+' '.join(reasons)
  else:
    # We should trust...  All is well!
    return


