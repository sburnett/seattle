# Copyright 2008 The Tor Project, Inc.  See LICENSE for licensing information.
# Copyright 2010 The Update Framework.  See LICENSE for licensing information.

import binascii
import calendar
import re
import string
import time

import tuf.util
import tuf.checkjson

json = tuf.util.import_json()


S = tuf.checkjson


# Note that in the schema definitions below, the S.Obj types allow additional
# keys which are not defined. Thus, they additions to them will be easily
# backwards compatible with clients that are already deployed.

# A date, in YYYY-MM-DD HH:MM:SS format.
TIME_SCHEMA = S.RE(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}')
# A hash, base64-encoded
HASH_SCHEMA = S.RE(r'[a-fA-F0-9]+')

HASHDICT_SCHEMA = S.DictOf(
    keySchema=S.AnyStr(),
    valSchema=HASH_SCHEMA)

# A hexadecimal value.
HEX_SCHEMA = S.RE(r'[a-fA-F0-9]+')
# A base-64 encoded value
BASE64_SCHEMA = S.RE(r'[a-zA-Z0-9\+\/]+')
# An RSA key; subtype of PUBKEY_SCHEMA.
RSAKEY_SCHEMA = S.Obj(
    keytype=S.Str("rsa"),
    keyval=S.Obj(
        e=BASE64_SCHEMA,
        n=BASE64_SCHEMA))
# Any public key.
PUBKEY_SCHEMA = S.Obj(
    keytype=S.AnyStr(),
    keyval=S.Any())

KEYID_SCHEMA = HASH_SCHEMA
SIG_METHOD_SCHEMA = S.AnyStr()
RELPATH_SCHEMA = PATH_PATTERN_SCHEMA = S.AnyStr()
URL_SCHEMA = S.AnyStr()
VERSION_SCHEMA = S.ListOf(S.Any()) #XXXX WRONG
LENGTH_SCHEMA = S.Int(lo=0)
THRESHOLD_SCHEMA = S.Int(lo=1)
ROLENAME_SCHEMA = S.AnyStr()

# Info that describes both metadata and target files.
FILEINFO_SCHEMA = S.Obj(
    length=LENGTH_SCHEMA,
    hashes=HASHDICT_SCHEMA,
    custom=S.Opt(S.Obj()))

FILEDICT_SCHEMA = S.DictOf(
    keySchema=RELPATH_SCHEMA,
    valSchema=FILEINFO_SCHEMA)

# A single signature of an object.  Indicates the signature, the id of the
# signing key, and the signing method.
# I debated making the signature schema not contain the key id and instead have
# the signatures of a file be a dictionary with the key being the keyid and the
# value being the the signature schema without the keyid. That would be under
# the argument that a key should only be able to sign a file once. However,
# one can imagine that maybe a key wants to sign multiple times with different
# signature methods.
SIGNATURE_SCHEMA = S.Obj(
    keyid=KEYID_SCHEMA,
    method=SIG_METHOD_SCHEMA,
    sig=BASE64_SCHEMA)

# A signable object.
SIGNABLE_SCHEMA = S.Obj(
    signed=S.Any(),
    signatures=S.ListOf(SIGNATURE_SCHEMA))

KEYDICT_SCHEMA = S.DictOf(
    keySchema=KEYID_SCHEMA,
    valSchema=PUBKEY_SCHEMA)

ROLE_SCHEMA = S.Obj(
    keyids=S.ListOf(KEYID_SCHEMA),
    threshold=THRESHOLD_SCHEMA,
    paths=S.Opt(S.ListOf(RELPATH_SCHEMA)))

# A RoleDict: indicates a dict of roles.
ROLEDICT_SCHEMA = S.DictOf(
    keySchema=ROLENAME_SCHEMA,
    valSchema=ROLE_SCHEMA)

# The root: indicates root keys and top-level roles.
ROOT_SCHEMA = S.Obj(
    _type=S.Str("Root"),
    ts=TIME_SCHEMA,
    expires=TIME_SCHEMA,
    keys=KEYDICT_SCHEMA,
    roles=ROLEDICT_SCHEMA)

# Targets. Indicates targets and delegates target paths to other roles.
TARGETS_SCHEMA = S.Obj(
    _type=S.Str("Targets"),
    ts=TIME_SCHEMA,
    expires=TIME_SCHEMA,
    targets=FILEDICT_SCHEMA,
    delegations=S.Opt(S.Obj(
        keys=KEYDICT_SCHEMA,
        roles=ROLEDICT_SCHEMA)))

# A Release: indicates the latest versions of all metadata (except timestamp).
RELEASE_SCHEMA = S.Obj(
    _type=S.Str("Release"),
    ts=TIME_SCHEMA,
    expires=TIME_SCHEMA,
    meta=FILEDICT_SCHEMA)

# A Timestamp: indicates the latest version of the release file.
TIMESTAMP_SCHEMA = S.Obj(
    _type=S.Str("Timestamp"),
    ts=TIME_SCHEMA,
    expires=TIME_SCHEMA,
    meta=FILEDICT_SCHEMA)

MIRROR_SCHEMA = S.Obj(
    urlbase=URL_SCHEMA,
    metapath=RELPATH_SCHEMA,
    targetspath=RELPATH_SCHEMA,
    metacontent=S.ListOf(PATH_PATTERN_SCHEMA),
    targetscontent=S.ListOf(PATH_PATTERN_SCHEMA),
    custom=S.Opt(S.Obj()))

# A Mirrorlist: indicates all the live mirrors, and what documents they
# serve.
MIRRORLIST_SCHEMA = S.Obj(
    _type=S.Str("Mirrors"),
    ts=TIME_SCHEMA,
    expires=TIME_SCHEMA,
    mirrors=S.ListOf(MIRROR_SCHEMA))


class MetaFile(object):
    """Base class for all metadata files."""

    info = None

    def __eq__(self, other):
        return isinstance(other, MetaFile) and self.info == other.info

    def __ne__(self, other):
        return not self.__eq__(other)

    def __getattr__(self, name):
        """Allow all metafile objects to have their interesting attributes
           referred to directly without the info dict. The info dict is just
           to be able to do the __eq__ comparison generically.
        """
        if name in self.info:
            return self.info[name]
        raise AttributeError, name


class TimestampFile(MetaFile):

    def __init__(self, ts, expires, meta_files):
        self.info = {}
        self.info['ts'] = ts
        self.info['expires'] = expires
        self.info['meta'] = meta_files

    @staticmethod
    def from_meta(obj):
        # TODO: must be validated.
        ts = parse_time(obj['ts'])
        expires = parse_time(obj['expires'])
        meta_files = obj['meta']
        return TimestampFile(ts, expires, meta_files)

    @staticmethod
    def make_meta(meta_filedict):

        result = {'_type' : 'Timestamp'}
        # TODO: set the expires time another way.
        result['ts'] = format_time(time.time())
        result['expires'] = format_time(time.time() + 3600 * 24 * 365)
        result['meta'] = meta_filedict

        TIMESTAMP_SCHEMA.check_match(result)
        return result


class RootFile(MetaFile):

    def __init__(self, ts, expires, keys, roles):
        self.info = {}
        self.info['ts'] = ts
        self.info['expires'] = expires
        self.info['keys'] = keys
        self.info['roles'] = roles

    @staticmethod
    def from_meta(obj):
        # TODO: must be validated.
        ts = parse_time(obj['ts'])
        expires = parse_time(obj['expires'])
        keys = obj['keys']
        roles = obj['roles']
        return RootFile(ts, expires, keys, roles)

    @staticmethod
    def make_meta(keyids, roledict, expiration_seconds):
        result = {'_type' : 'Root'}
        # TODO: set the expires time another way.
        result['ts'] = format_time(time.time())
        result['expires'] = format_time(time.time() + expiration_seconds)
        result['keys'] = keyids
        result['roles'] = roledict
        ROOT_SCHEMA.check_match(result)
        return result


class ReleaseFile(MetaFile):

    def __init__(self, ts, expires, meta_files):
        self.info = {}
        self.info['ts'] = ts
        self.info['expires'] = expires
        self.info['meta'] = meta_files

    @staticmethod
    def from_meta(obj):
        # TODO: must be validated.
        ts = parse_time(obj['ts'])
        expires = parse_time(obj['expires'])
        meta_files = obj['meta']
        return ReleaseFile(ts, expires, meta_files)

    @staticmethod
    def make_meta(meta_filedict):
        result = {'_type' : 'Release'}
        # TODO: set the expires time another way.
        result['ts'] = format_time(time.time())
        result['expires'] = format_time(time.time() + 3600 * 24 * 365)
        result['meta'] = meta_filedict

        RELEASE_SCHEMA.check_match(result)
        return result


class TargetsFile(MetaFile):

    def __init__(self, ts, expires, targets=None, delegations=None):
        if targets is None:
            targets = {}
        if delegations is None:
            delegations = {}
        self.info = {}
        self.info['ts'] = ts
        self.info['expires'] = expires
        self.info['targets'] = targets
        self.info['delegations'] = delegations

    @staticmethod
    def from_meta(obj):
        # TODO: must be validated.
        ts = parse_time(obj['ts'])
        expires = parse_time(obj['expires'])
        targets = obj.get('targets')
        delegations = obj.get('delegations')
        return TargetsFile(ts, expires, targets, delegations)

    @staticmethod
    def make_meta(targets_filedict=None, delegations=None):
        if targets_filedict is None and delegations is None:
            raise tuf.Error("We don't allow completely empty targets metadata.")

        result = {'_type' : 'Targets'}
        # TODO: set the expires time another way.
        result['ts'] = format_time(time.time())
        result['expires'] = format_time(time.time() + 3600 * 24 * 365)
        if targets_filedict is not None:
            result['targets'] = targets_filedict
        if delegations is not None:
            result['delegations'] = delegations

        TARGETS_SCHEMA.check_match(result)
        return result


class MirrorsFile(MetaFile):

    def __init__(self, ts, expires):
        self.info = {}
        self.info['ts'] = ts
        self.info['expires'] = expires

    @staticmethod
    def from_meta(obj):
        raise NotImplementedError

    @staticmethod
    def make_meta():
        raise NotImplementedError


def canonical_str_encoder(s):
    s = '"%s"' % re.sub(r'(["\\])', r'\\\1', s)
    if isinstance(s, unicode):
        return s.encode("utf-8")
    else:
        return s


def _encode_canonical(obj, outf):
    # Helper for encode_canonical.  Older versions of json.encoder don't
    # even let us replace the separators.

    if isinstance(obj, basestring):
        outf(canonical_str_encoder(obj))
    elif obj is True:
        outf("true")
    elif obj is False:
        outf("false")
    elif obj is None:
        outf("null")
    elif isinstance(obj, (int, long)):
        outf(str(obj))
    elif isinstance(obj, (tuple, list)):
        outf("[")
        if len(obj):
            for item in obj[:-1]:
                _encode_canonical(item, outf)
                outf(",")
            _encode_canonical(obj[-1], outf)
        outf("]")
    elif isinstance(obj, dict):
        outf("{")
        if len(obj):
            items = obj.items()
            items.sort()
            for k, v in items[:-1]:
                outf(canonical_str_encoder(k))
                outf(":")
                _encode_canonical(v, outf)
                outf(",")
            k, v = items[-1]
            outf(canonical_str_encoder(k))
            outf(":")
            _encode_canonical(v, outf)
        outf("}")
    else:
        raise tuf.FormatException("I can't encode %r" % obj)


def encode_canonical(obj, outf=None):
    """Encode the object obj in canoncial JSon form, as specified at
       http://wiki.laptop.org/go/Canonical_JSON .  It's a restricted
       dialect of json in which keys are always lexically sorted,
       there is no whitespace, floats aren't allowed, and only quote
       and backslash get escaped.  The result is encoded in UTF-8,
       and the resulting bits are passed to outf (if provided), or joined
       into a string and returned.

       >>> encode_canonical("")
       '""'
       >>> encode_canonical([1, 2, 3])
       '[1,2,3]'
       >>> encode_canonical([])
       '[]'
       >>> encode_canonical({"A": [99]})
       '{"A":[99]}'
       >>> encode_canonical({"x" : 3, "y" : 2})
       '{"x":3,"y":2}'
    """

    result = None
    if outf == None:
        result = [ ]
        outf = result.append

    _encode_canonical(obj, outf)

    if result is not None:
        return "".join(result)


def make_signable(obj):
    if not isinstance(obj, dict) or 'signed' not in obj:
        return { 'signed' : obj, 'signatures' : [] }
    else:
        return obj


def format_time(t):
    """Encode the time 't' in YYYY-MM-DD HH:MM:SS format.

    >>> format_time(1221265172)
    '2008-09-13 00:19:32'
    """
    return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(t))


def parse_time(s):
    """Parse a time 's' in YYYY-MM-DD HH:MM:SS format."""
    try:
        return calendar.timegm(time.strptime(s, "%Y-%m-%d %H:%M:%S"))
    except ValueError:
        raise tuf.FormatException("Malformed time %r", s)


def format_base64(h):
    """Return the base64 encoding of h with whitespace and = signs omitted."""
    return binascii.b2a_base64(h).rstrip("=\n ")


def parse_base64(s):
    """Parse a base64 encoding with whitespace and = signs omitted. """
    extra = len(s) % 4
    if extra:
        padding = "=" * (4 - extra)
        s += padding
    try:
        return binascii.a2b_base64(s)
    except binascii.Error:
        raise tuf.FormatException("Invalid base64 encoding")


# TODO(jsamuel): The copy avoids the problem, but bad style to use mutable
# objects as default argument values.
def read_config_file(fname, needKeys=(), optKeys=(), preload={}):
    parsed = preload.copy()
    result = {}
    execfile(fname, parsed)

    for k in needKeys:
        try:
            result[k] = parsed[k]
        except KeyError:
            raise tuf.FormatException("Missing value for %s in %s" % (k, fname))

    for k in optKeys:
        try:
            result[k] = parsed[k]
        except KeyError:
            pass

    return result


def make_file_info_meta(length, hashes, custom=None):
    # TODO: Check fields.
    # TODO: we currently require the hashes to already be in HASHES_SCHEMA,
    # which means the hashes must have been run through format_hash(digest).
    fileinfo = {'length' : length, 'hashes' : hashes}
    if custom is not None:
        fileinfo['custom'] = custom

    FILEINFO_SCHEMA.check_match(fileinfo)

    return fileinfo


def make_role_meta(keyids, threshold, paths=None):
    """keyids is a list of key ids"""

    result = {}
    result['keyids'] = keyids
    result['threshold'] = threshold
    if paths is not None:
        result['paths'] = paths

    ROLE_SCHEMA.check_match(result)

    return result


SCHEMAS_BY_TYPE = {
    'Root' : ROOT_SCHEMA,
    'Targets' : TARGETS_SCHEMA,
    'Release' : RELEASE_SCHEMA,
    'Timestamp' : TIMESTAMP_SCHEMA,
    'Mirrors' : MIRRORLIST_SCHEMA
    }


CLASSES_BY_TYPE = {
    'Root' : RootFile,
    'Targets' : TargetsFile,
    'Release' : ReleaseFile,
    'Timestamp' : TimestampFile,
    'Mirrors' : MirrorsFile
    }


def expected_meta_type(meta_name):
    if meta_name.startswith('targets'):
        return 'Targets'
    else:
        return string.capwords(meta_name)


# TODO: rename  to check_signable_obj_format ?
def check_signed_obj_format(obj):
    # Returns signing role on success, raises FormatException or ValueError
    # on error. 

    SIGNABLE_SCHEMA.check_match(obj)
    try:
        tp = obj['signed']['_type']
    except KeyError:
        raise tuf.FormatException("Untyped object")
    try:
        schema = SCHEMAS_BY_TYPE[tp]
    except KeyError:
        raise tuf.FormatException("Unrecognized type %r" % tp)
    schema.check_match(obj['signed'])

    if tp not in ['Root', 'Mirrors', 'Timestamp', 'Targets', 'Release']:
        raise ValueError("Unknown signed object type %r" % tp)

    return tp.lower()
