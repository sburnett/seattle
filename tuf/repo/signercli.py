#!/usr/bin/env python
# Copyright 2008 The Tor Project, Inc.  See LICENSE for licensing information.
# Copyright 2010 The Update Framework.  See LICENSE for licensing information.

import os
import getopt
import getpass
import sys

from tuf.repo import signerlib
import tuf.util

json = tuf.util.import_json()


DEFAULT_KEYSTORE_FILENAME = tuf.util.user_filename("secret_keys")

DEFAULT_META_DIR = '.'


_keystore = None


def _get_keystore(options=(), prompt='Password: '):
    global _keystore
    if _keystore is None:
        password = _get_password(prompt)
        for o, v in options:
            if o == "--keystore":
                filename = v
                break
        else:    
            filename = DEFAULT_KEYSTORE_FILENAME
        if password:
            _keystore = signerlib.get_keystore(filename, password)
        else:
            _keystore = signerlib.get_keystore(filename, encrypted=False)
    return _keystore


def _get_password(prompt="Password: ", confirm=False):
    while 1:
        pwd = getpass.getpass(prompt, sys.stderr)
        if not confirm:
            return pwd
        pwd2 = getpass.getpass("Confirm: ", sys.stderr)
        if pwd == pwd2:
            return pwd
        else:
            print "Mismatch; try again."


def _get_key_ids(options):
    keyids = []
    for o, v in options:
        if o == "--keyid":
            keyids.append(v)
    return keyids


def _get_meta_dir(options):
    for o, v in options:
        if o == "--metadir":
            return v
    return DEFAULT_META_DIR


def _sign_and_write(meta, fuzzy_keys, filename, options):
    """Sign metadata and write it to a file. Overwrites the original file.
       If any of the keyids have already signed the file, the old signatures
       of those keyids will be replaced.
    """
    keystore = _get_keystore(options)
    meta = signerlib.sign_meta(meta, fuzzy_keys, keystore)
    signerlib.write_metadata_file(meta, filename)


def _get_meta_filenames(meta_dir):
    if meta_dir is None:
        meta_dir = '.'
    filenames = {}
    filenames['root'] = os.path.join(meta_dir, 'root.txt')
    filenames['targets'] = os.path.join(meta_dir, 'targets.txt')
    filenames['release'] = os.path.join(meta_dir, 'release.txt')
    filenames['timestamp'] = os.path.join(meta_dir, 'timestamp.txt')
    return filenames


def makeroot(args):
    """
    Creates the root.txt file.
    """
    options, args = getopt.getopt(args, "", ["keyid=", "metadir=", "keystore="])
    fuzzy_keys = _get_key_ids(options)
    meta_dir = _get_meta_dir(options)
    filenames = _get_meta_filenames(meta_dir)

    if len(args) != 1:
        usage()

    config_file = args[0]
    keystore = _get_keystore()

    meta = signerlib.generate_root_meta(config_file, keystore)
    _sign_and_write(meta, fuzzy_keys, filenames['root'], options)


def maketargets(args):
    """
    The targets must exist at the same path they should on the repo.
    
    This takes a list targets. We're not worrying about custom metadata at the
    moment. It's allowed to not provide keys.
    """
    options, args = getopt.getopt(args, "", ["keyid=", "metadir=", "parentdir=", "keystore=", "rolename="])
    opts = dict(options)
    fuzzy_keys = _get_key_ids(options)

    if len(args) < 1:
        usage()

    target_files = args

    meta = signerlib.generate_targets_meta(target_files)
    role = opts.get('--rolename', '')
    if not role:
        meta_dir = _get_meta_dir(options)
        filenames = _get_meta_filenames(meta_dir)
        dest = filenames['targets']
    else:
        dest = os.path.sep.join(meta, opts['--parentdir'], opts['--rolename'])
        dest += '.txt'
    _sign_and_write(meta, fuzzy_keys, dest, options)


def makerelease(args):
    """
    The minimum metadata must exist. This is root.txt and targets.txt.
    """
    options, args = getopt.getopt(args, "", ["keyid=", "metadir=", "keystore="])
    fuzzy_keys = _get_key_ids(options)
    meta_dir = _get_meta_dir(options)
    filenames = _get_meta_filenames(meta_dir)

    if len(args):
        usage()

    meta = signerlib.generate_release_meta(meta_dir)
    _sign_and_write(meta, fuzzy_keys, filenames['release'], options)


def maketimestamp(args):
    """
    The release.txt file must exist.
    """
    options, args = getopt.getopt(args, "", ["keyid=", "metadir=", "keystore="])
    fuzzy_keys = _get_key_ids(options)
    meta_dir = _get_meta_dir(options)
    filenames = _get_meta_filenames(meta_dir)

    if args:
        usage()

    meta = signerlib.generate_timestamp_meta(filenames['release'])
    _sign_and_write(meta, fuzzy_keys, filenames['timestamp'], options)


def sign(args):
    """
    The release.txt file must exist.
    """
    options, args = getopt.getopt(args, "", ["keyid=", "keystore="])
    fuzzy_keys = _get_key_ids(options)

    if len(args) != 1 or len(fuzzy_keys) == 0:
        usage()

    filename = args[0]

    meta = signerlib.read_metadata_file(filename)
    _sign_and_write(meta, fuzzy_keys, filename, options)


def changepass(args):
    keystore = _get_keystore(prompt="Old password: ")
    new_pass = _get_password("New password: ")
    keystore.set_password(new_pass)
    keystore.save()


def genkey(args):
    options, args = getopt.getopt(args, "", ["keystore="])
    keystore = _get_keystore(options)
    # TODO: Allow specifying key length.
    signerlib.generate_key(bits=None, keystore=keystore)


def listkeys(args):
    options, args = getopt.getopt(args, "", ["keystore="])
    keystore = _get_keystore(options)
    for key in keystore.iterkeys():
        print key.get_key_id()


def dumpkey(args):
    options, args = getopt.getopt(args, "", ["keystore=", "include-secret"])

    includeSecret = False
    for o, v in options:
        if o == '--include-secret':
            includeSecret = True

    ks = _get_keystore(options)

    keys = []
    if len(args):
        keys = [signerlib.get_key(ks, a) for a in args]
    else:
        keys = list(ks.iterkeys())

    for k in keys:
        data = k.get_meta(private=includeSecret)
        print "Key(", json.dumps(data, indent=2, sort_keys=True), ")"

def delegate(args):
    # parse the options
    options, args = getopt.getopt(args, "", ["keyid=", "keystore=", "repo="])
    fuzzy_keys = _get_key_ids(options)
    parentrole, role, rolekey, paths = args[0], args[1], args[2], args[3:]
    _keystore = _get_keystore(options)
    metadir = _get_meta_dir(options)
    targets_file = _get_meta_filenames(metadir)['targets']
    # get the key from the keystore
    key = signerlib.get_key(_keystore, rolekey)
    # extract the metadata from the targets file
    targets_metadata = signerlib.read_metadata_file(targets_file)
    # extract the delegations structure if it exists
    delegations = targets_metadata.get('delegations', {})
    # update the keys field
    keys = delegations.get('keys', {})
    keys[rolekey] = key.get_meta()
    delegations['keys'] = keys
    # update the roles field
    roles = delegations.get('roles', {})
    roles[role] = tuf.formats.make_role_meta([key.get_key_id()], 1, paths)
    delegations['roles'] = roles
    # update the larger metadata structure
    targets_metadata['delegations'] = delegations
    # and try to write the whole thing
    meta = tuf.formats.make_signable(targets_metadata)
    _sign_and_write(meta, fuzzy_keys, targets_file, options)
	
# TODO: a "remove signature" function? Should that be in signerlib?


def usage():
    print "Known commands:"
    print "  genkey"
    print "  listkeys"
    print "  changepass"
    print "  dumpkey [--include-secret] keyid"
    print "  makeroot [--keyid= ...] configfile"
    print "  maketargets [--keyid= ...] target ..."
    print "  makerelease [--keyid= ...]"
    print "  maketimestamp [--keyid= ...]"
    print "  sign --keyid= [--keyid= ...] file"
    print "  delegate --keyid= [--keyid= ...] parentrole role rolekey paths"
    sys.exit(1)


def main():
    if len(sys.argv) < 2:
        usage()
    cmd = sys.argv[1]
    args = sys.argv[2:]
    if cmd in ["genkey", "listkeys", "changepass", "dumpkey", "makeroot",
               "maketargets", "makerelease", "maketimestamp", "sign", "delegate"]:
        try:
            globals()[cmd](args)
        except tuf.BadPassword:
            print >> sys.stderr, "Password incorrect."
    else:
        usage()


if __name__ == '__main__':
    main()
