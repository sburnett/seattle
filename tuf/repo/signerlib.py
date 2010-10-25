# Copyright 2008 The Tor Project, Inc.  See LICENSE for licensing information.
# Copyright 2010 The Update Framework.  See LICENSE for licensing information.

import ConfigParser
import os
import sys

import tuf.formats
import tuf.keys
import tuf.log
import tuf.repo.keystore
import tuf.sig
import tuf.util

logger = tuf.log.get_logger()

json = tuf.util.import_json()


def get_keystore(filename, password=None, encrypted=True):
    return tuf.repo.keystore.KeyStore(filename, password=password,
                                      encrypted=encrypted)


# TODO(jsamuel): Have it raise an exception instead of exiting (or change the
# function name).
def get_key(keydb, keyid):
    if keyid is not None:
        keys = keydb.get_keys_fuzzy(keyid)
    if len(keys) < 1:
        logger.error("No such key.\nI wanted")
        logger.error("keyid='%s...'" % keyid)
        logger.error("I only know about:")
        for k in keydb.iterkeys():
            logger.error("  %s" % k.get_key_id())
        sys.exit(1)
    elif len(keys) > 1:
        logger.error("Multiple keys match.  Possibilities are:")
        for k in keys:
            logger.error("  %s" % k.get_key_id())
        sys.exit(1)
    else:
        return keys[0]


def _read_config_file(filename):
    """Return a dictionary where the keys are section names and the values
       are dictionaries of keys/values in that section.
    """
    config = ConfigParser.RawConfigParser()
    config.read(filename)
    configdict = {}
    for section in config.sections():
        configdict[section] = {}
        for key, value in config.items(section):
            if key in ['threshold', 'seconds', 'minutes', 'days', 'hours']:
                value = int(value)
            elif key in ['keyids']:
                value = value.split(',')
            configdict[section][key] = value
    return configdict


def generate_root_meta(config_file, public_key_keydb):
    """
    Creates the root metadata.
    """
    config = _read_config_file(config_file)

    roledict = {}
    keydict = {}

    for rolename in ['root', 'targets', 'release', 'timestamp']:
        if rolename not in config:
            raise tuf.Error("No '%s' section found in config file." % rolename)
        keyids = []
        for fuzzy_keyid in config[rolename]['keyids']:
            key = get_key(public_key_keydb, keyid=fuzzy_keyid)
            keyid = key.get_key_id()
            if keyid not in keydict:
                keydict[keyid] = key.get_meta()
            if keyid in keyids:
                raise tuf.Error("Same keyid listed twice: %s", keyid)
            keyids.append(keyid)
        role_meta = tuf.formats.make_role_meta(keyids,
                                             config[rolename]['threshold'])
        roledict[rolename] = role_meta

    exp = config['expiration']
    expiration_seconds = (exp['seconds'] + 60 * exp['minutes'] +
                          3600 * exp['hours'] + 3600 * 24 * exp['days'])

    root_meta = tuf.formats.RootFile.make_meta(keydict, roledict,
                                               expiration_seconds)
    return tuf.formats.make_signable(root_meta)


def _get_file_info_meta(filename):
    length, hashes = tuf.util.get_file_details(filename)
    custom = None
    return tuf.formats.make_file_info_meta(length, hashes, custom)


# TODO: 'size' instead of 'length'?


def generate_targets_meta(target_files=None, targets_filedict=None,
                          delegations_keydb=None):
    """
    The targets must exist at the same path they should on the repo.
    
    This takes a list targets. We're not worrying about custom metadata at the
    moment. It's allowed to not provide keys.
    """
    if targets_filedict is None:
        filedict = {}
    else:
        filedict = targets_filedict.copy()

    if target_files is not None:
        for target in target_files:
            filedict[target] = _get_file_info_meta(target)

    delegations_meta = None
    if delegations_keydb is not None:
        keys = {}
        roles = {}
        for rolename in delegations_keydb.get_role_names():
            threshold = delegations_keydb.get_role_threshold(rolename)
            keyids = delegations_keydb.get_role_keyids(rolename)
            targetpaths = delegations_keydb.get_role_paths(rolename)
            for keyid in keyids:
                key = delegations_keydb.get_key(keyid)
                keys[keyid] = key.get_meta(private=False)
            roles[rolename] = {'threshold' : threshold, 'keyids' : keyids,
                               'paths' : targetpaths}
        delegations_meta = {'keys' : keys, 'roles' : roles}

    targets_meta = tuf.formats.TargetsFile.make_meta(
        targets_filedict=filedict, delegations=delegations_meta)

    return tuf.formats.make_signable(targets_meta)


def generate_release_meta(meta_dir):
    """
    The minimum metadata must exist. This is root.txt and targets.txt. This
    will also look for a targets/ delegation metadata directory and the
    resulting release file will list all files in that directory.
    """
    root_filename = os.path.join(meta_dir, 'root.txt')
    targets_filename = os.path.join(meta_dir, 'targets.txt')
    filedict = {}
    filedict['root.txt'] = _get_file_info_meta(root_filename)
    filedict['targets.txt'] = _get_file_info_meta(targets_filename)

    meta_targets_dir = os.path.join(meta_dir, 'targets')
    if os.path.exists(meta_targets_dir) and os.path.isdir(meta_targets_dir):
        for dirpath, _, files in os.walk(meta_targets_dir):
            for basename in files:
                if not dirpath.startswith(meta_dir):
                    raise tuf.Error('Confused while walking targets/')
                meta_path = os.path.join(dirpath, basename)
                meta_name = meta_path[len(meta_dir):].lstrip('/')
                if not meta_name.startswith('targets/'):
                    raise tuf.Error('Confused while figuring out meta_name: %s' % meta_name)
                filedict[meta_name] = _get_file_info_meta(meta_path)

    release_meta = tuf.formats.ReleaseFile.make_meta(filedict)
    return tuf.formats.make_signable(release_meta)


def generate_timestamp_meta(release_filename, compressions=()):
    """
    The release.txt file must exist.
    """
    fileinfo = {}
    fileinfo['release.txt'] = _get_file_info_meta(release_filename)
    for ext in compressions:
        compress_filename = release_filename + '.' + ext
        fileinfo['release.txt.' + ext] = _get_file_info_meta(compress_filename)
    timestamp_meta = tuf.formats.TimestampFile.make_meta(fileinfo)
    return tuf.formats.make_signable(timestamp_meta)


def write_metadata_file(meta, filename):
    logger.info("Writing to %s" % filename)
    f = open(filename, 'w')
    json.dump(meta, f, indent=1, sort_keys=True)
    f.write('\n')
    f.close()


def read_metadata_file(filename):
    return tuf.util.load_json_file(filename)


def sign_meta(meta, keyids, keydb):
    """
    Sign a file. If any of the keyids have already signed the file, the old
    signature will be replaced.
    """
    signable = tuf.formats.make_signable(meta)

    for keyid in keyids:
        key = get_key(keydb, keyid=keyid)
        print("Signing with key %s" % key.get_key_id())
        tuf.sig.add_signature(signable, key)

    tuf.formats.check_signed_obj_format(signable)

    return signable


def verify_meta(meta, keystore):
    """
    Verify signatures on a file. Doesn't verify that they are trusted, just
    that the signatures are valid.
    """
    role = None
    status = tuf.sig.get_signature_status(meta, keystore, role)

    return status


def generate_key(bits=None, keystore=None):
    key = tuf.keys.RSAKey.generate(bits)
    logger.info("Generated new key: %s" % key.get_key_id())
    if keystore is not None:
        keystore.add_key(key)
        keystore.save()
    return key
