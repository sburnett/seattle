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
    """Helper to store private keys in encrypted files.

    Originally this stored the keys in one file- we've changed that so that it
    instead encrypts them separately, naming them according to their id value.

    This changes the semantics of the system considerably- first, the fname
    passed in was originally treated as a filename. We now treat it as the name
    of a directory.

    Secondly, it no longer makes sense to provide access to keys which do not
    match the given decryption key.

    Thirdly, the semantics of adding keys has changed. It does not make sense to 
    have only one key for the entire keystore, and as a result we're requiring 
    that the password be set at the point where the key is added.
    """

    def __init__(self, dirname):
        tuf.keydb.KeyDB.__init__(self)
        self._dirname = dirname

    def load(self, passwords):
        logger.debug(passwords)
        logger.info("Loading private keys from %r...", self._dirname)

        # check to make sure the directory exists and we have access
        if not os.path.exists(self._dirname):
            logger.info("...no such directory.")

        # test for access here

        # now get the list of filenames containing keys from the directory
        is_keypath = lambda x: x.endswith('.key')
        keypaths = filter(is_keypath, os.listdir(self._dirname))

        # decrypt the keys we can
        for keypath in keypaths:
            raw_contents = open(os.path.join(self._dirname, keypath), 'rb').read()
            for pw in passwords:
                try: jsondata = _decrypt(raw_contents, pw)
                except: continue
                keydata = json.loads(jsondata)
                key = tuf.keys.RSAKey(keydata)
                self.add_key(key, pw, keyid=keypath[:-4])
                logger.info("Loaded key %s", key.get_key_id())
                break

        # go home
        logger.info("Done.")

    def save(self):
        logger.info("Saving private keys into %r...", self._dirname)

        # check to make sure the directory exists and we have access
        if not os.path.exists(self._dirname):
            logger.info("...no such directory.")
            os.mkdir(self._dirname)

        for key_id, key in self._keys.items():
            f = open(os.path.join(self._dirname, key_id + '.key'), 'w')
            f.write(_encrypt(json.dumps(key.key), self._passwords[key_id]))
            f.close()
        logger.info("Done.")

def _encrypt(value, password):
	salt, iv, ciphertext = evpy.cipher.encrypt(value, password)
	return hexlify(salt) + "@@@@" + hexlify(iv) + "@@@@" + hexlify(ciphertext)

def _decrypt(value, password):
	salt, iv, ciphertext = value.split('@@@@')
	return evpy.cipher.decrypt(unhexlify(salt), unhexlify(iv), unhexlify(ciphertext), password)
