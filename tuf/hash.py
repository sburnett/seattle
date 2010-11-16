# Copyright 2008 The Tor Project, Inc.  See LICENSE for licensing information.
# Copyright 2010 The Update Framework.  See LICENSE for licensing information.

import binascii

import tuf.log

logger = tuf.log.get_logger()


# This will be set to the appropriate function depending on whether hashlib
# or pycrypto is used.
_get_digest_obj = None


def _create_get_digest_obj_func(library):
    if library == 'hashlib':
        import hashlib
        def _get_digest_obj(algorithm):
            try:
                return hashlib.new(algorithm)
            except ValueError:
                raise tuf.UnsupportedAlgorithmError(algorithm)
    else:
        raise tuf.Error('Unknown hash library: %s' % library)

    return _get_digest_obj


try:
    # Python <=2.4 does not have hashlib.
    _get_digest_obj = _create_get_digest_obj_func('hashlib')
except ImportError:
    try:
        _get_digest_obj = _create_get_digest_obj_func('pycrypto')
    except ImportError:
        # This is fatal, we'll have no way to generate hashes.
        raise


def parse_hash(hash_hex, algorithm):
    try:
        digest = binascii.a2b_hex(hash_hex)
    except binascii.Error:
        raise tuf.FormatException("Invalid hex encoding")
    hashlen = Digest(algorithm).digest_size

    if len(digest) != hashlen:
        raise tuf.FormatException("Bad hash length")

    return digest


class Digest(object):
    def __init__(self, algorithm):
        self._algorithm = algorithm
        self._obj = _get_digest_obj(algorithm)

    def update(self, data):
        if isinstance(data, str):
            self._obj.update(data)
        elif isinstance(data, unicode):
            self._obj.update(data.encode("utf-8"))
        else:
            self._obj.update(str(data))
        return self

    def update_filename(self, filename):
        fp = open(filename, 'rb')
        try:
            self.update_file_obj(fp)
        finally:
            fp.close()
        return self

    def update_file_obj(self, fp):
        # Defensively seek to beginning, as there's no case where we don't
        # intend to start from the beginning of the file.
        fp.seek(0)
        while 1:
            data = fp.read(4096)
            if not data:
                break
            self.update(data)
        return self

    def format(self):
        """Return the hex encoding of the digest."""
        return self._obj.hexdigest()

    def digest(self):
        return self._obj.digest()

    def _get_digest_size(self):
        return self._obj.digest_size

    digest_size = property(_get_digest_size)
