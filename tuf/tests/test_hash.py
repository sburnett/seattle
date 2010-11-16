# Copyright 2010 The Update Framework.  See LICENSE for licensing information.

import os
import StringIO
import tempfile
import unittest

import tuf.hash


class Test(unittest.TestCase):

    def _run_with_all_hash_libraries(self, test_func):
        tuf.hash._get_digest_obj = tuf.hash._create_get_digest_obj_func('hashlib')
        test_func()
        tuf.hash._get_digest_obj = tuf.hash._create_get_digest_obj_func('pycrypto')
        test_func()

    def test_md5_update(self):
        self._run_with_all_hash_libraries(self._do_md5_update)

    def _do_md5_update(self):
        d_obj = tuf.hash.Digest('md5')
        self.assertEqual(d_obj.format(), 'd41d8cd98f00b204e9800998ecf8427e')
        d_obj.update('a')
        self.assertEqual(d_obj.format(), '0cc175b9c0f1b6a831c399e269772661')
        d_obj.update(u'bbb')
        self.assertEqual(d_obj.format(), 'f034e93091235adbb5d2781908e2b313')
        d_obj.update('')
        self.assertEqual(d_obj.format(), 'f034e93091235adbb5d2781908e2b313')

    def test_sha1_update(self):
        self._run_with_all_hash_libraries(self._do_sha1_update)

    def _do_sha1_update(self):
        d_obj = tuf.hash.Digest('sha1')
        self.assertEqual(d_obj.format(), 'da39a3ee5e6b4b0d3255bfef95601890afd80709')
        d_obj.update('a')
        self.assertEqual(d_obj.format(), '86f7e437faa5a7fce15d1ddcb9eaeaea377667b8')
        d_obj.update(u'bbb')
        self.assertEqual(d_obj.format(), 'd7bfa42fc62b697bf6cf1cda9af1fb7f40a27817')
        d_obj.update('')
        self.assertEqual(d_obj.format(), 'd7bfa42fc62b697bf6cf1cda9af1fb7f40a27817')

    def test_sha256_update(self):
        self._run_with_all_hash_libraries(self._do_sha256_update)

    def _do_sha256_update(self):
        d_obj = tuf.hash.Digest('sha256')
        self.assertEqual(d_obj.format(), 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855')
        d_obj.update('a')
        self.assertEqual(d_obj.format(), 'ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb')
        d_obj.update(u'bbb')
        self.assertEqual(d_obj.format(), '01d162a5c95d4698c0a3e766ae80d85994b549b877ed275803725f43dadc83bd')
        d_obj.update('')
        self.assertEqual(d_obj.format(), '01d162a5c95d4698c0a3e766ae80d85994b549b877ed275803725f43dadc83bd')

    def test_unsupported_algorithm(self):
        self._run_with_all_hash_libraries(self._do_unsupported_algorithm)

    def _do_unsupported_algorithm(self):
        self.assertRaises(tuf.UnsupportedAlgorithmError, tuf.hash.Digest, 'bogus')

    def test_digest_size(self):
        self._run_with_all_hash_libraries(self._do_digest_size)

    def _do_digest_size(self):
        self.assertEqual(16, tuf.hash.Digest('md5').digest_size)
        self.assertEqual(20, tuf.hash.Digest('sha1').digest_size)
        self.assertEqual(32, tuf.hash.Digest('sha256').digest_size)

    def test_parse_hash(self):
        self._run_with_all_hash_libraries(self._do_parse_hash)

    def _do_parse_hash(self):
        for algorithm in ['md5', 'sha1', 'sha256']:
            d_obj = tuf.hash.Digest(algorithm)
            d_obj.update('abc')
            hash_hex = d_obj.format()
            hash_bytes = tuf.hash.parse_hash(hash_hex, algorithm)
            self.assertEqual(d_obj.digest(), hash_bytes)

    def test_update_filename(self):
        self._run_with_all_hash_libraries(self._do_update_filename)

    def _do_update_filename(self):
        data = 'abcdefgh' * 4096
        fd, filename = tempfile.mkstemp()
        try:
            os.write(fd, data)
            os.close(fd)
            for algorithm in ['md5', 'sha1', 'sha256']:
                d_obj_truth = tuf.hash.Digest(algorithm)
                d_obj_truth.update(data)
                d_obj = tuf.hash.Digest(algorithm)
                d_obj.update_filename(filename)
                self.assertEqual(d_obj_truth.digest(), d_obj.digest())
        finally:
            os.remove(filename)

    def test_update_file_obj(self):
        self._run_with_all_hash_libraries(self._do_update_file_obj)

    def _do_update_file_obj(self):
        data = 'abcdefgh' * 4096
        file_obj = StringIO.StringIO()
        file_obj.write(data)
        for algorithm in ['md5', 'sha1', 'sha256']:
            d_obj_truth = tuf.hash.Digest(algorithm)
            d_obj_truth.update(data)
            d_obj = tuf.hash.Digest(algorithm)
            # Note: we don't seek because the update_file_obj call is supposed
            # to always seek to the beginning.
            d_obj.update_file_obj(file_obj)
            self.assertEqual(d_obj_truth.digest(), d_obj.digest())


if __name__ == "__main__":
    unittest.main()
