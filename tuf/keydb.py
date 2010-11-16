# Copyright 2008 The Tor Project, Inc.  See LICENSE for licensing information.
# Copyright 2010 The Update Framework.  See LICENSE for licensing information.

import re

import tuf.keys


def get_parent_role(rolename):
    """Gets the name of the parent role."""
    # TODO: Raise a specific exception if no role by the name exists?
    #self._validate_rolename(rolename)
    parts = rolename.split('/')
    return '/'.join(parts[:-1])


def get_all_parent_roles(rolename):
    """Gets a list of roles that are parents of rolename.
    
    Given the rolename 'a/b/c/d', returns the list:
        ['a', 'a/b', 'a/b/c']
    """
    # TODO: Raise a specific exception if no role by the name exists?
    #self._validate_rolename(rolename)
    parent_roles = []
    parts = rolename.split('/')
    for i in range(1, len(parts)):
        parent_roles.append('/'.join(parts[:i]))
    return parent_roles


class KeyDB:
    """
    A KeyDB holds public keys, indexed by their key IDs.
    TODO: This is more than a KeyDB, as it has role info. So, either change
    it or rename it.
    """

    def __init__(self):
        self._keys = {}
        self._roles = {}
	self._passwords = {}

    @staticmethod
    def create_from_root(root_meta):
        keydb = KeyDB()
        for keyid, key_meta in root_meta.keys.items():
            key = tuf.keys.RSAKey.from_meta(key_meta)
	    keydb.add_key(key, keyid)
        for rolename, roleinfo in root_meta.roles.items():
            keydb.add_role(rolename, roleinfo)
        return keydb

    def add_key(self, key, password, keyid=None):
        """
        If keyid is provided, this will ensure it is the correct keyid for
        the key and will raise an exception if it is not.
        'key' is a key object.
        """
        if keyid is not None and keyid != key.get_key_id():
            raise tuf.Error("Incorrect keyid %s, expected %s." %
                            (key.get_key_id(), keyid))
        keyid = key.get_key_id()
        if keyid in self._keys:
            raise tuf.KeyAlreadyExistsError("keyid: %s" % keyid)
        self._keys[keyid] = key
	self._passwords[keyid] = password
	

    def _validate_rolename(self, rolename):
        if rolename != rolename.strip():
            raise tuf.InvalidNameError(
                "Invalid rolename. Cannot start or end with whitespace: '%s'" %
                rolename)
        if rolename.startswith('/') or rolename.endswith('/'):
            raise tuf.InvalidNameError(
                "Invalid rolename. Cannot start or end with '/': %s" % rolename)

    def role_exists(self, rolename):
        return rolename in self._roles

    def add_role(self, rolename, roleinfo, require_parent=True):
        """Role follows ROLE_SCHEMA."""
        self._validate_rolename(rolename)
        if rolename in self._roles:
            raise tuf.RoleAlreadyExistsError("Role already exists.")

        # Make sure that the delegating role exists. This should be just a
        # sanity check and not a security measure.
        if require_parent and '/' in rolename:
            parent_role = '/'.join(rolename.split('/')[:-1])
            if parent_role not in self._roles:
                raise tuf.Error("Parent role does not exist: %s" % parent_role)

        # TODO: validate roleinfo
        # TODO: make sure every referenced keyid has already been added.
        self._roles[rolename] = roleinfo

    def remove_role(self, rolename):
        """Removes a role's, including its delegations.
        
        Unused keys are left in the keydb.
        """
        self._validate_rolename(rolename)
        self.remove_delegated_roles(rolename)
        if rolename in self._roles:
            del self._roles[rolename]

    def remove_delegated_roles(self, rolename):
        """Removes a role's delegations (leaving the rest of the role alone).
        
        Unused keys are left in the keydb. All levels of delegation are
        removed, not just the directly delegated roles.
        """
        self._validate_rolename(rolename)
        for name in self.get_role_names():
            if name.startswith(rolename) and name != rolename:
                del self._roles[name]

    def get_role_names(self):
        return self._roles.keys()

    def get_role_keyids(self, rolename):
        try:
            roleinfo = self._roles[rolename]
        except KeyError:
            raise tuf.UnknownRoleError(rolename)
        return roleinfo['keyids']

    def get_role_threshold(self, rolename):
        try:
            roleinfo = self._roles[rolename]
        except KeyError:
            raise tuf.UnknownRoleError(rolename)
        return roleinfo['threshold']

    def get_role_paths(self, rolename):
        try:
            roleinfo = self._roles[rolename]
        except KeyError:
            raise tuf.UnknownRoleError(rolename)
        # Paths won't exist for non-target roles.
        return roleinfo['paths']

    def get_delegated_role_names(self, rolename):
        """Gets the immediate delegations of a role."""
        delegated_roles = []
        rolename_with_slash = rolename + '/'
        for name in self.get_role_names():
            if name.startswith(rolename_with_slash) and name != rolename:
                delegated_roles.append(name)
        return delegated_roles

    def get_key(self, keyid):
        try:
            return self._keys[keyid]
        except KeyError:
            raise tuf.UnknownKeyError('Key: %s' % keyid)

    def get_keys_fuzzy(self, keyid):
        r = []
        for k, v in self._keys.iteritems():
            if k.startswith(keyid):
                r.append(v)
        return r

    def iterkeys(self):
        return self._keys.itervalues()


class Keylist(KeyDB):

    def __init__(self):
        KeyDB.__init__(self)

    def add_from_keylist(self, obj):
        for keyitem in obj['keys']:
            key = keyitem['key']

            try:
                key = tuf.keys.RSAKey.from_meta(key)
            except tuf.FormatException, e:
                #LOG skipping key.
                continue

            self.add_key(key)


_rolePathCache = {}


def role_path_matches(rolePath, path):
    """Return true iff the relative path in the filesystem 'path' conforms
       to the pattern 'rolePath': a path that a given key is
       authorized to sign.  Patterns are allowed to contain * to
       represent one or more characters in a filename, and ** to
       represent any level of directory structure.

    >>> role_path_matches("a/b/c/", "a/b/c/")
    True
    >>> role_path_matches("**/c.*", "a/b/c.txt")
    True
    >>> role_path_matches("**/c.*", "a/b/ctxt")
    False
    >>> role_path_matches("**/c.*", "a/b/c.txt/foo")
    False
    >>> role_path_matches("a/*/c", "a/b/c")
    True
    >>> role_path_matches("a/*/c", "a/b/c.txt")
    False
    >>> role_path_matches("a/*/c", "a/b/c.txt") #Check cache
    False
    """
    try:
        regex = _rolePathCache[rolePath]
    except KeyError:
        orig = rolePath
        # remove duplicate slashes.
        rolePath = re.sub(r'/+', '/', rolePath)
        # escape, then ** becomes .*
        rolePath = re.escape(rolePath).replace(r'\*\*', r'.*')
        # * becomes [^/]*
        rolePath = rolePath.replace(r'\*', r'[^/]*')
        # and no extra text is allowed.
        rolePath += "$"
        regex = _rolePathCache[orig] = re.compile(rolePath)
    return regex.match(path) != None
