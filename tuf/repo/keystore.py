# Copyright 2008 The Tor Project, Inc.  See LICENSE for licensing information.
# Copyright 2010 The Update Framework.  See LICENSE for licensing information.

import os
import struct
from binascii import hexlify, unhexlify

import evpy.cipher

import tuf.keydb
import tuf.keys
import tuf.log
import tuf.util

logger = tuf.log.get_logger()

json = tuf.util.import_json()


class KeyStore(tuf.keydb.KeyDB):
    """Helper to store private keys in an encrypted file."""

    def __init__(self, fname, password=None, encrypted=True):
        tuf.keydb.KeyDB.__init__(self)

        self._loaded = False
        self._fname = fname
        self._encrypted = encrypted
        self._passwd = password

        logger.info("Loading private keys from %r...", self._fname)
        if not os.path.exists(self._fname):
            logger.info("...no such file.")
            return

        contents = open(self._fname, 'rb').read()
        if self._encrypted:
            contents = _decrypt(contents, self._passwd)

        listOfKeys = json.loads(contents)
        if not listOfKeys.has_key('keys'):
            listOfKeys['keys'] = []
        for obj in listOfKeys['keys']:
            key = tuf.keys.RSAKey.from_meta(obj)
            self.add_key(key)
            logger.info("Loaded key %s", key.get_key_id())

    def set_password(self, passwd):
        self._passwd = passwd

    def clear_password(self):
        self._passwd = None

    def save(self):
        logger.info("Saving private keys into %r...", self._fname)
        keys = {'keys' : [key.get_meta(private=True) for
                          key in self._keys.values()]}
        contents = json.dumps(keys)
        if self._encrypted:
            contents = _encrypt(contents, self._passwd)
        tuf.util.replace_file(self._fname, contents)
        logger.info("Done.")

def _encrypt(value, password):
	salt, iv, ciphertext = evpy.cipher.encrypt(value, password)
	return hexlify(salt) + "@@@@" + hexlify(iv) + "@@@@" + hexlify(ciphertext)

def _decrypt(value, password):
	salt, iv, ciphertext = value.split('@@@@')
	return evpy.cipher.decrypt(unhexlify(salt), unhexlify(iv), unhexlify(ciphertext), password)
