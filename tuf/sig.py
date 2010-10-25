# Copyright 2008 The Tor Project, Inc.  See LICENSE for licensing information.
# Copyright 2010 The Update Framework.  See LICENSE for licensing information.

import tuf.formats


# The hash algorithm to use for signing.
SIGNATURE_HASH_ALG = 'sha256'


class SignatureStatus(object):
    """Represents the outcome of checking signature(s) on an object."""

    def __init__(self, threshold, good, bad, unrecognized, unauthorized, uknown_method):
        # The required threshold of signatures by the role's keys.
        self.threshold = threshold
        # keyids for all the valid signatures
        self.good = good[:]
        # keyids for the invalid signatures (we had the key, and it failed).
        self.bad = bad[:]
        # keyids for signatures where we didn't recognize the key
        self.unrecognized = unrecognized[:]
        # keyids for signatures where we recognized the key, but it doesn't
        # seem to be allowed to sign this kind of document.
        self.unauthorized = unauthorized[:]
        self.uknown_method = uknown_method[:]

    def __str__(self):
        return ("threshold: %s / good: %s / bad %s / unrecognized: %s / "
                "unauthorized: %s / unknown method: %s" %
                (self.threshold, self.good, self.bad, self.unrecognized,
                 self.unauthorized, self.uknown_method))

    def is_valid(self):
        """Return true iff we got at least 'threshold' good signatures."""
        if self.threshold is None or self.threshold <= 0:
            raise tuf.Error("Invalid threshold: %s", self.threshold)
        return len(self.good) >= self.threshold

    def may_need_new_keys(self):
        """Return true iff downloading a new set of keys might tip this
           signature status over to 'valid.'"""
        return len(self.unrecognized) or len(self.unauthorized)


def check_signatures(signable, keydb, role=None):
    """Given an object conformant to SIGNED_SCHEMA and a set of public keys
       in keyDB, verify the signed object in 'signed'.
       
       This will raise tuf.BadSignature if the signed data isn't fully trusted.
    """
    status = get_signature_status(signable, keydb, role)
    if not status.is_valid():
        raise tuf.BadSignature(str(status))
    return status

def get_signature_status(signable, keydb, role):
    """Given an object conformant to SIGNABLE_SCHEMA and a set of public keys
       in keyDB, verify the signed object in 'signed'.
       
       This does not raise an exception.
    """

    #tuf.formats.SIGNABLE_SCHEMA.check_match(signable)

    good_sigs = []
    bad_sigs = []
    unknown_sigs = []
    untrusted_sigs = []
    unknown_method_sigs = []

    signed = signable['signed']
    signatures = signable['signatures']

    data = tuf.formats.encode_canonical(signed)

    for signature in signatures:
        sig = signature['sig']
        keyid = signature['keyid']
        method = signature['method']

        try:
            key = keydb.get_key(keyid)
        except tuf.UnknownKeyError:
            unknown_sigs.append(keyid)
            continue

        try:
            valid_sig = key.verify(method, sig, data)
        except tuf.UnknownMethod:
            unknown_method_sigs.append(keyid)
            continue

        if valid_sig:
            if role is not None:
                try:
                    if keyid not in keydb.get_role_keyids(role):
                        untrusted_sigs.append(keyid)
                        continue
                except tuf.UnknownRoleError:
                    # TODO: Is this the correct way to indicate this?
                    unknown_sigs.append(keyid)
                    continue
            good_sigs.append(keyid)
        else:
            bad_sigs.append(keyid)

    if role is not None:
        threshold = keydb.get_role_threshold(role)
    else:
        threshold = None

    return SignatureStatus(threshold, good_sigs, bad_sigs, unknown_sigs,
                           untrusted_sigs, unknown_method_sigs)


def add_signature(signable, key):
    """Add an element to the signatures of signable, containing a new signature
       of the "signed" part.
    """

    #tuf.formats.SIGNABLE_SCHEMA.check_match(signable)

    signed = tuf.formats.encode_canonical(signable["signed"])
    signatures = signable['signatures']

    keyid = key.get_key_id()

    signatures = [ s for s in signatures if s['keyid'] != keyid ]

    method, sig = key.sign(signed)
    signatures.append({ 'keyid' : keyid,
                        'method' : method,
                        'sig' : sig })

    signable['signatures'] = signatures
