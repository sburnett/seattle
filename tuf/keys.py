# Copyright 2008 The Tor Project, Inc.  See LICENSE for licensing information.
# Copyright 2010 The Update Framework.  See LICENSE for licensing information.

import binascii
import os

# These require PyCrypto.
#import Crypto.PublicKey.RSA
import evpy.signature
import evpy.envelope

import tuf.formats
import tuf.hash
import tuf.util

json = tuf.util.import_json()


KEY_ID_HASH_ALGORITHM = 'sha256'

DEFAULT_RSA_KEY_LENGTH = 2048


class PublicKey:
    """Abstract base class for public keys."""

    def __init__(self):
        self._roles = []

    def format(self):
        raise NotImplementedError()

    def sign(self, data=None, digest=None):
        # returns a list of method,signature tuples.
        raise NotImplementedError()

    def verify(self, method, data, signature):
        # returns True, False, or raises UnknownMethod.
        raise NotImplementedError()

    def get_key_id(self):
        raise NotImplementedError()


if hex(1L).upper() == "0X1L":
    def int_to_binary(number):
        """Convert an int or long into a big-endian series of bytes.
        """
        # This "convert-to-hex, then use binascii" approach may look silly,
        # but it's over 10x faster than the Crypto.Util.number approach.
        h = hex(long(number))
        h = h[2:-1]
        if len(h) % 2:
            h = "0" + h
        return binascii.a2b_hex(h)
elif hex(1L).upper() == "0X1":
    def int_to_binary(number):
        "Variant for future versions of pythons that don't append 'L'."
        h = hex(long(number))
        h = h[2:]
        if len(h) % 2:
            h = "0" + h
        return binascii.a2b_hex(h)
else:
    import Crypto.Util.number
    int_to_binary = Crypto.Util.number.long_to_bytes
    assert None


def binary_to_int(binary):
    """Convert a big-endian series of bytes into a long.
    """
    return long(binascii.b2a_hex(binary), 16)


def int_to_base64(number):
    """Convert an int or long to a big-endian base64-encoded value."""
    return tuf.formats.format_base64(int_to_binary(number))


def base64_to_int(number):
    """Convert a big-endian base64-encoded value to a long."""
    return binary_to_int(tuf.formats.parse_base64(number))


def _pkcs1_padding(m, size):
    # I'd rather use OAEP+, but apparently PyCrypto barely supports
    # signature verification, and doesn't seem to support signature
    # verification with nondeterministic padding.  "argh."

    s = [ "\x00\x01", "\xff" * (size - 3 - len(m)), "\x00", m ]
    r = "".join(s)
    return r


def _xor(a, b):
    if a:
        return not b
    else:
        return b


class RSAKey(PublicKey):
    """
    >>> k = RSAKey.generate(bits=512)
    >>> obj = k.format()
    >>> obj['keytype']
    'rsa'
    >>> base64_to_int(obj['keyval']['e'])
    65537L
    >>> k1 = RSAKey.from_meta(obj['keyval'])
    >>> k1.key.e == k.key.e
    True
    >>> k1.key.n == k.key.n
    True
    >>> k.get_key_id() == k1.get_key_id()
    True
    >>> s = { 'A B C' : "D", "E" : [ "F", "g", 99] }
    >>> method, sig = k.sign(obj=s)
    >>> k.check_signature(method, sig, obj=s)
    True
    >>> s2 = [ s ]
    >>> k.check_signature(method, sig, obj=s2)
    False
    """

    def __init__(self, key):
        PublicKey.__init__(self)
        try:
                self.key = key['keyval']
        except Exception:
                self.key = key
        self.keyid = None

    @staticmethod
    def generate(bits=None):
        """Generate a new RSA key, with modulus length 'bits'."""
        if bits is None:
            bits = DEFAULT_RSA_KEY_LENGTH
        key = list(evpy.envelope.keygen(bits))
        return RSAKey(key)

    @staticmethod
    def from_meta(obj):
        """Construct an RSA key from the output of the get_meta() method.
        """
        # obj must match RSAKEY_SCHEMA
        key = obj['keyval']
        #tuf.formats.RSAKEY_SCHEMA.check_match(obj)
        #n = base64_to_int(keyval['n'])
        #e = base64_to_int(keyval['e'])
        #if keyval.has_key('d'):
        #    d = base64_to_int(keyval['d'])
        #    p = base64_to_int(keyval['p'])
        #    q = base64_to_int(keyval['q'])
        #    #u = base64_to_int(keyval['u'])
        #    #key = Crypto.PublicKey.RSA.construct((n, e, d, p, q, u))
        #    key = Crypto.PublicKey.RSA.construct((n, e, d, p, q))
        #else:
        #    key = Crypto.PublicKey.RSA.construct((n, e))
        return RSAKey(key)

    def is_private_key(self):
        """Return true iff this key has private-key components"""
        return self.key[1] != None

    def get_meta(self, private=False):
        """Return a new object to represent this key in json format.
           If 'private', include private-key data.  If 'includeRoles',
           include role information.
        """
        #n = int_to_base64(self.key.n)
        #e = int_to_base64(self.key.e)
        #result = { 'keytype' : 'rsa',
        #           'keyval' : {'e' : e,
        #                       'n' : n } }
        #if private:
        #    result['keyval']['d'] = int_to_base64(self.key.d)
        #    result['keyval']['p'] = int_to_base64(self.key.p)
        #    result['keyval']['q'] = int_to_base64(self.key.q)
        #    #result['keyval']['u'] = int_to_base64(self.key.u)
	if private:
	        return {'keytype': 'rsa', 'keyval': self.key}
	else:
		return {'keytype': 'rsa', 'keyval': [str(self.key[0]), None]}

    def get_key_id(self):
        """Return the KeyID for this key.
        """
        if self.keyid == None:
            #json_format = tuf.formats.encode_canonical(self.get_meta())
            d_obj = tuf.hash.Digest(KEY_ID_HASH_ALGORITHM)
            d_obj.update(self.get_meta())
            self.keyid = d_obj.format()
        return self.keyid

    def sign(self, data):
        method = "evp"
        #d_obj = tuf.hash.Digest('sha256')
        #d_obj.update(data)
        #digest = d_obj.digest()
        #m = _pkcs1_padding(digest, (self.key.size() + 1) // 8)
        #sig = int_to_base64(self.key.sign(m, "")[0])
        if self.key[1]:
                sig = evpy.signature.sign(data, key=self.key[1])
        else:
                raise Exception("No private key defined for this key")
        return (method, binascii.hexlify(sig))

    def verify(self, method, sig, data):
        if method != "evp":
            raise tuf.UnknownMethod(method)
        #d_obj = tuf.hash.Digest('sha256')
        #d_obj.update(data)
        #digest = d_obj.digest()
        #sig = base64_to_int(sig)
        #m = _pkcs1_padding(digest, (self.key.size() + 1) // 8)
        return evpy.signature.verify(data, binascii.unhexlify(sig), key=self.key[0])
