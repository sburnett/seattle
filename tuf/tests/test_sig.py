import unittest

import tuf.keydb
import tuf.keys
import tuf.sig


KEYS = []


class Test(unittest.TestCase):

    def setUp(self):
        if not KEYS:
            for _ in range(3):
                KEYS.append(tuf.keys.RSAKey.generate(1024))

    def test_get_signature_status_no_role(self):
        signable = {'signatures' : [], 'signed' : 'test'}

        tuf.sig.add_signature(signable, KEYS[0])

        keydb = tuf.keydb.KeyDB()
        keydb.add_key(KEYS[0])

        # No specific role we're considering.
        sig_status = tuf.sig.get_signature_status(signable, keydb, None)

        self.assertEqual(None, sig_status.threshold)
        self.assertEqual([KEYS[0].get_key_id()], sig_status.good)
        self.assertEqual([], sig_status.bad)
        self.assertEqual([], sig_status.unrecognized)
        self.assertEqual([], sig_status.unauthorized)
        self.assertEqual([], sig_status.uknown_method)

        # Not allowed to call is_valid without having specified a role.
        self.assertRaises(tuf.Error, sig_status.is_valid)

    def test_get_signature_status_bad_sig(self):
        signable = {'signatures' : [], 'signed' : 'test'}

        tuf.sig.add_signature(signable, KEYS[0])
        signable['signed'] += 'signature no longer matches signed data'

        keydb = tuf.keydb.KeyDB()
        keydb.add_key(KEYS[0])
        threshold = 1
        roleinfo = tuf.formats.make_role_meta(
            [KEYS[0].get_key_id()], threshold)
        keydb.add_role('Root', roleinfo)

        sig_status = tuf.sig.get_signature_status(signable, keydb, 'Root')

        self.assertEqual(1, sig_status.threshold)
        self.assertEqual([], sig_status.good)
        self.assertEqual([KEYS[0].get_key_id()], sig_status.bad)
        self.assertEqual([], sig_status.unrecognized)
        self.assertEqual([], sig_status.unauthorized)
        self.assertEqual([], sig_status.uknown_method)

        self.assertFalse(sig_status.is_valid())

    def test_get_signature_status_uknown_method(self):
        signable = {'signatures' : [], 'signed' : 'test'}

        tuf.sig.add_signature(signable, KEYS[0])
        signable['signatures'][0]['method'] = 'fake-sig-method'

        keydb = tuf.keydb.KeyDB()
        keydb.add_key(KEYS[0])
        threshold = 1
        roleinfo = tuf.formats.make_role_meta(
            [KEYS[0].get_key_id()], threshold)
        keydb.add_role('Root', roleinfo)

        sig_status = tuf.sig.get_signature_status(signable, keydb, 'Root')

        self.assertEqual(1, sig_status.threshold)
        self.assertEqual([], sig_status.good)
        self.assertEqual([], sig_status.bad)
        self.assertEqual([], sig_status.unrecognized)
        self.assertEqual([], sig_status.unauthorized)
        self.assertEqual([KEYS[0].get_key_id()], sig_status.uknown_method)

        self.assertFalse(sig_status.is_valid())

    def test_get_signature_status_single_key(self):
        signable = {'signatures' : [], 'signed' : 'test'}

        tuf.sig.add_signature(signable, KEYS[0])

        keydb = tuf.keydb.KeyDB()
        keydb.add_key(KEYS[0])
        threshold = 1
        roleinfo = tuf.formats.make_role_meta(
            [KEYS[0].get_key_id()], threshold)
        keydb.add_role('Root', roleinfo)

        sig_status = tuf.sig.get_signature_status(signable, keydb, 'Root')

        self.assertEqual(1, sig_status.threshold)
        self.assertEqual([KEYS[0].get_key_id()], sig_status.good)
        self.assertEqual([], sig_status.bad)
        self.assertEqual([], sig_status.unrecognized)
        self.assertEqual([], sig_status.unauthorized)
        self.assertEqual([], sig_status.uknown_method)

        self.assertTrue(sig_status.is_valid())

    def test_get_signature_status_below_threshold(self):
        signable = {'signatures' : [], 'signed' : 'test'}

        tuf.sig.add_signature(signable, KEYS[0])

        keydb = tuf.keydb.KeyDB()
        keydb.add_key(KEYS[0])
        threshold = 2
        roleinfo = tuf.formats.make_role_meta(
            [KEYS[0].get_key_id(), KEYS[2].get_key_id()], threshold)
        keydb.add_role('Root', roleinfo)

        sig_status = tuf.sig.get_signature_status(signable, keydb, 'Root')

        self.assertEqual(2, sig_status.threshold)
        self.assertEqual([KEYS[0].get_key_id()], sig_status.good)
        self.assertEqual([], sig_status.bad)
        self.assertEqual([], sig_status.unrecognized)
        self.assertEqual([], sig_status.unauthorized)
        self.assertEqual([], sig_status.uknown_method)

        self.assertFalse(sig_status.is_valid())

    def test_get_signature_status_below_threshold_unrecognized_sigs(self):
        signable = {'signatures' : [], 'signed' : 'test'}

        # Two keys sign it, but only one of them will be trusted.
        tuf.sig.add_signature(signable, KEYS[0])
        tuf.sig.add_signature(signable, KEYS[2])

        keydb = tuf.keydb.KeyDB()
        keydb.add_key(KEYS[0])
        keydb.add_key(KEYS[1])
        threshold = 2
        roleinfo = tuf.formats.make_role_meta(
            [KEYS[0].get_key_id(), KEYS[1].get_key_id()], threshold)
        keydb.add_role('Root', roleinfo)

        sig_status = tuf.sig.get_signature_status(signable, keydb, 'Root')

        self.assertEqual(2, sig_status.threshold)
        self.assertEqual([KEYS[0].get_key_id()], sig_status.good)
        self.assertEqual([], sig_status.bad)
        self.assertEqual([KEYS[2].get_key_id()], sig_status.unrecognized)
        self.assertEqual([], sig_status.unauthorized)
        self.assertEqual([], sig_status.uknown_method)

        self.assertFalse(sig_status.is_valid())

    def test_get_signature_status_below_threshold_unauthorized_sigs(self):
        signable = {'signatures' : [], 'signed' : 'test'}

        # Two keys sign it, but one of them is only trusted for a different
        # role.
        tuf.sig.add_signature(signable, KEYS[0])
        tuf.sig.add_signature(signable, KEYS[1])

        keydb = tuf.keydb.KeyDB()
        keydb.add_key(KEYS[0])
        keydb.add_key(KEYS[1])
        threshold = 2
        roleinfo = tuf.formats.make_role_meta(
            [KEYS[0].get_key_id(), KEYS[2].get_key_id()], threshold)
        keydb.add_role('Root', roleinfo)
        roleinfo = tuf.formats.make_role_meta(
            [KEYS[1].get_key_id(), KEYS[2].get_key_id()], threshold)
        keydb.add_role('Release', roleinfo)

        sig_status = tuf.sig.get_signature_status(signable, keydb, 'Root')

        self.assertEqual(2, sig_status.threshold)
        self.assertEqual([KEYS[0].get_key_id()], sig_status.good)
        self.assertEqual([], sig_status.bad)
        self.assertEqual([], sig_status.unrecognized)
        self.assertEqual([KEYS[1].get_key_id()], sig_status.unauthorized)
        self.assertEqual([], sig_status.uknown_method)

        self.assertFalse(sig_status.is_valid())

    def test_check_signatures_no_role(self):
        signable = {'signatures' : [], 'signed' : 'test'}

        tuf.sig.add_signature(signable, KEYS[0])

        keydb = tuf.keydb.KeyDB()
        keydb.add_key(KEYS[0])

        # No specific role we're considering. It's invalid to use the
        # function check_signatures without a role specified because
        # check_signatures is checking trust, as well.
        args = (signable, keydb, None)
        self.assertRaises(tuf.Error, tuf.sig.check_signatures, *args)

    def test_check_signatures_single_key(self):
        signable = {'signatures' : [], 'signed' : 'test'}

        tuf.sig.add_signature(signable, KEYS[0])

        keydb = tuf.keydb.KeyDB()
        keydb.add_key(KEYS[0])
        threshold = 1
        roleinfo = tuf.formats.make_role_meta(
            [KEYS[0].get_key_id()], threshold)
        keydb.add_role('Root', roleinfo)

        # This will call is_valid() and raise an exception if it's not.
        sig_status = tuf.sig.check_signatures(signable, keydb, 'Root')
        self.assertTrue(sig_status.is_valid())

    def test_check_signatures_unrecognized_sig(self):
        signable = {'signatures' : [], 'signed' : 'test'}

        # Two keys sign it, but only one of them will be trusted.
        tuf.sig.add_signature(signable, KEYS[0])
        tuf.sig.add_signature(signable, KEYS[2])

        keydb = tuf.keydb.KeyDB()
        keydb.add_key(KEYS[0])
        keydb.add_key(KEYS[1])
        threshold = 2
        roleinfo = tuf.formats.make_role_meta(
            [KEYS[0].get_key_id(), KEYS[1].get_key_id()], threshold)
        keydb.add_role('Root', roleinfo)

        args = (signable, keydb, 'Root')
        self.assertRaises(tuf.BadSignature, tuf.sig.check_signatures, *args)

    def test_add_signature(self):
        signable = {'signatures' : [], 'signed' : 'test'}

        tuf.sig.add_signature(signable, KEYS[0])

        self.assertEqual(1, len(signable['signatures']))
        signature = signable['signatures'][0]
        self.assertEqual(KEYS[0].get_key_id(), signature['keyid'])

        tuf.sig.add_signature(signable, KEYS[1])

        self.assertEqual(2, len(signable['signatures']))
        signature = signable['signatures'][1]
        self.assertEqual(KEYS[1].get_key_id(), signature['keyid'])

    def test_SignatureStatus_may_need_new_keys(self):
        # TODO: Implement.
        pass

    def test_signable_has_invalid_format(self):
        # TODO: Implement.
        pass


if __name__ == "__main__":
    unittest.main()
