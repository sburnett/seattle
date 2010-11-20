# Copyright 2010 The Update Framework.  See LICENSE for licensing information.

import logging


class SettingsHolder(object):

    def __init__(self):
        # Set a directory that should be used for all temporary files. If this
        # is None, then the system default will be used. The system default
        # will also be used if a directory path set here is invalid or
        # unusable.
        self.temp_dir = None

        self.log_level = logging.ERROR

        # If None, then logging will be done to stderr.
        self.log_filename = None

        # The directory under which metadata for all repositories will be
        # stored. This is not a simple cache because each repository's root of
        # trust (root.txt) will need to already be stored below here and should
        # not be deleted. At a minimum, each key in the mirrors dictionary
        # below should have a directory under this repo_meta_dir which already
        # exists and within that directory should have the file 'cur/root.txt'.
        # This must be set!
        self.repo_meta_dir = None


settings = SettingsHolder()
