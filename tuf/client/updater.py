# Copyright 2010 The Update Framework.  See LICENSE for licensing information.
"""
This module is intended to be the only TUF module that software update systems
need to interact with in their code. It provides classes which represent
repositories and downloadable targets.
"""

import os
import time
import warnings

import tuf.formats
import tuf.keydb
import tuf.log
import tuf.mirrors
import tuf.conf
import tuf.sig
import tuf.util

#import logging
logger = tuf.log.get_logger()
#logger.setLevel(logging.DEBUG)


DEFAULT_DL_JOB_GENERATOR = tuf.mirrors.mirror_download_job_generator


class Repository(object):
    """A repository that can be used for downloading target files.
        
    Attributes:
        download_job_generator: The job generator for downloading targets.
        fileinfo: A cache of lengths and hashes of stored metadata files.
        keydb: The keydb that includes all current key/role/trust info.
        meta: Trusted metadata that has been read from files.
        meta_dir: The directories where trusted metadata is stored.
        mirrors: The mirrors from which metadata and targets are available.
        name: The name of the repository.
    """

    def __init__(self, name, mirrors,
                 download_job_generator=DEFAULT_DL_JOB_GENERATOR):
        """Constructor.
        
        In order to use a repository, the following directories must already
        exist under the tuf.conf.settings.repo_meta_dir directory:
            {name}/cur
            {name}/prev
        and, at a minimum, the root metadata must exist (not necessarily with
        any signatures) at:
            {name}/cur/root.txt
            
        Args:
            name: The name to use for this repository. This will also be the
                name of the directory that will be used for storing metadata.
            mirrors: A dictionary of mirrors that contain this repository's
                content.
            download_job_generator: A generator that returns DownloadJob
                instances which can be used for downloading a target.
        """
        self.name = str(name)
        self.mirrors = mirrors
        self.download_job_generator = download_job_generator

        self.meta = {}
        self.meta['cur'] = {} # Current trusted/verified metadata.
        self.meta['prev'] = {} # Previous trusted/verified.

        # The keys are paths, the values are fileinfo meta. This is used to
        # determine whether a metadata file has changed and so needs to be
        # downloaded.
        self.fileinfo = {}

        repos_dir = tuf.conf.settings.repo_meta_dir
        self.meta_dir = {}
        self.meta_dir['cur'] = os.path.join(repos_dir, name, 'cur')
        self.meta_dir['prev'] = os.path.join(repos_dir, name, 'prev')

        self.keydb = None

        # Load current and previous metadata.
        for mset in ['cur', 'prev']:
            for mname in ['root', 'timestamp', 'release', 'targets']:
                self._load_metadata_from_file(mset, mname)

        if "root" not in self.meta['cur']:
            raise tuf.Error("No root of trust! Couldn't find root.txt file.")

    def __str__(self):
        return self.name

    def _load_metadata_from_file(self, cur_or_prev, meta_name):
        """Loads current or previous metadata if there is a local file.
        
        Doesn't load the metadata from file if the metadata is already loaded.
        Doesn't load the metadata if it is 'cur' (current) metadata and any
        targets specified are not allowed.
        
        Args:
            cur_or_prev: 'cur' or 'prev', depending on whether one wants to
                load the currently or previously trusted metadata file.
            meta_name: The name of the metadata. This is a role name. This
                should not end in '.txt'.
        """
        mdir = self.meta_dir[cur_or_prev]
        mtype = tuf.formats.expected_meta_type(meta_name)

        rel_path = meta_name + '.txt'
        path = os.path.join(mdir, rel_path)
        if not os.path.exists(path):
            raise Exception("Couldn't load %s" % path)
	    #logger.debug("Couldn't load %s" % path)
            #return
       
        json_obj = tuf.util.load_json_file(path)

        meta_format = tuf.formats.CLASSES_BY_TYPE[mtype]
        signed = json_obj['signed']
        meta_obj = meta_format.from_meta(signed)
     	   #if cur_or_prev == 'cur':
                # Reject the metadata if any specified targets aren't allowed.
                # TODO: Do we really care to do this since we check the paths
                # before handing out Target objects? Not checking this here
                # would allow a parent role to restrict the paths of a
                # delegated role such that the delegated role doesn't need to
                # resign their file if there are targets not allowed anymore.
                #if isinstance(meta_obj, tuf.formats.TargetsFile):
                #    try:
                #        self._ensure_all_targets_allowed(meta_name, meta_obj)
                #    except tuf.RepoError:
                #        logger.exception("Couldn't load %s", path)
                #        return
        self.meta[cur_or_prev][meta_name] = meta_obj
        if cur_or_prev == 'cur':
            if meta_name == 'root':
                self._rebuild_keydb()
            elif isinstance(meta_obj, tuf.formats.TargetsFile):
                self.keydb.remove_delegated_roles(meta_name)
                self._import_delegations(meta_name)

    def _rebuild_keydb(self):
        """Rebuilds the keydb from the current, trusted root metadata."""
        # TODO: Clobbering this means all delegated metadata files will need
        # to be reloaded. We need to signal that (e.g. remove those entries
        # from meta['cur'] so they get reloaded from disk).
        self.keydb = tuf.keydb.KeyDB.create_from_root(self.meta['cur']['root'])

    def _update_fileinfo(self, rel_path):
        """Updates the fileinfo dictionary for the metadata at rel_path."""
        # In case we delayed loading of the metadata and didn't do it in
        # __init__ (such as with delegated metadata), then get the file
        # info now.
        path = os.path.join(self.meta_dir['cur'], rel_path)
        if not os.path.exists(path):
            self.fileinfo[rel_path] = None
            return
        length, hashes = tuf.util.get_file_details(path)
        fileinfo_meta = tuf.formats.make_file_info_meta(length, hashes)
        self.fileinfo[rel_path] = fileinfo_meta

    def _update_metadata(self, meta_name, want_hashes=None, want_length=None,
                         compression=None):
        """Downloads, verifies, and 'installs' metadata.
        
        Raises:
            tuf.RepoError: The metadata could not be updated. This is not
                specific to a single failure but rather indicates that all
                possible ways to update the metadata have been tried and
                failed.
        """
        rel_path = meta_name + ".txt"
        dl_rel_path = rel_path
        if compression == 'gzip':
            dl_rel_path = dl_rel_path + '.gz'

        for job in self.download_job_generator(
            'meta', dl_rel_path, self.mirrors, wantHashes=want_hashes,
            wantLength=want_length):

            try:
            	temp_file_obj = job.download()
            except tuf.DownloadError, err:
                logger.warn("Download failed from %s" % job.url)
                continue

            if compression:
                temp_file_obj.set_compression(compression)

            json_obj = tuf.util.load_json_string(temp_file_obj.read())

            try:
                status = tuf.sig.check_signatures(json_obj, self.keydb,
                                                  role=meta_name)
                logger.debug("Good sig on %s / %s" % (job.url, status))
            except tuf.BadSignature, err:
                logger.warn("Bad sig on %s / %s" % (job.url, err))
            else:
                break
        else:
            raise tuf.RepoError("Unable to update %s" % rel_path)

        # The metadata has been verified. Move it into place.
        # TODO: Move the 'cur' metadata file to the 'prev' directory, if there
        # is a current metadata file.
        dest_path = os.path.join(self.meta_dir['cur'], rel_path)
        # TODO: the pathname might not be windows-friendly. That is, they might
        # be forward slashes from urls rather than windows backslashes.
        tuf.util.ensure_parent_dir(dest_path)
        temp_file_obj.move(dest_path)

        meta_type = tuf.formats.expected_meta_type(meta_name)
        meta_format = tuf.formats.CLASSES_BY_TYPE[meta_type]
        try:
            new_meta_obj = meta_format.from_meta(json_obj['signed'])
        except Exception, err:
            raise tuf.RepoError("Unable to load %s after update: %s %s" %
                                (rel_path, type(err), err))

        # Reject the metadata if any specified targets aren't allowed.
        if isinstance(new_meta_obj, tuf.formats.TargetsFile):
            self._ensure_all_targets_allowed(meta_name, new_meta_obj)

        cur_meta_obj = self.meta['cur'].get(meta_name)

        logger.debug("Updated metadata: %s" % meta_name)
        self.meta['prev'][meta_name] = cur_meta_obj
        self.meta['cur'][meta_name] = new_meta_obj

    def _ensure_all_targets_allowed(self, meta_name, meta_obj):
        if meta_name == 'targets':
            return
        # Create a list of pattern lists. Each pattern list is the pattern list
        # of a role in the delegation chain to this role whose metadata is
        # being updated.
        pattern_lists = []
        for parent_role in tuf.keydb.get_all_parent_roles(meta_name):
            if parent_role == 'targets':
                continue
            pattern_lists.append((parent_role,
                                  self.keydb.get_role_paths(parent_role)))
        for targetpath in meta_obj.targets.keys():
            for parent_role, patterns in pattern_lists:
                if not tuf.util.path_in_patterns(targetpath, patterns):
                    msg = ("Role %s specifies target '%s', which is not an "
                           "allowed path according to delegation by %s." %
                            (meta_name, targetpath, parent_role))
                    raise tuf.RepoError(msg)

    def _fileinfo_has_changed(self, rel_path, new_file_info):
        """Determine whether stored a metadata file differs from new file info.
        
        new_file_info should only be None if this is for updating root.txt
        without having release.txt available.
        """
        if rel_path not in self.fileinfo:
            self._update_fileinfo(rel_path)

        if self.fileinfo[rel_path] is None:
            return True

        if new_file_info is None:
            return True

        cur_file_info = self.fileinfo[rel_path]

        if cur_file_info['length'] != new_file_info['length']:
            return True

        # Now compare hashes. Note that the reason we can't just do a simple
        # equality check on the fileinfo dicts is that we want to support the
        # case where the hash algorithms listed in the metadata have changed
        # without having that result in considering all files as needing to be
        # updated, or not all hash algorithms listed can be calculated on the
        # specific client.
        for alg, hashstr in new_file_info['hashes'].items():
            # We're only looking for a single match. This isn't a security
            # check, we just want to prevent unnecessary downloads.
            if hashstr == cur_file_info['hashes'][alg]:
                return False

        return True

    def _rotate_metadata_files(self, meta_name):
        rel_path = meta_name + '.txt'
        prev_path = os.path.join(self.meta_dir['prev'], rel_path)
        cur_path = os.path.join(self.meta_dir['cur'], rel_path)
        if os.path.exists(prev_path):
            os.remove(prev_path)
        if os.path.exists(cur_path):
            os.rename(cur_path, prev_path)

    def _delete_metadata(self, meta_name):
        """Removes all (current) knowledge of specific metadata."""
        if meta_name == 'root':
            return
        # Get rid of the current metadata file.
        self._rotate_metadata_files(meta_name)
        # Remove knowledge of the role.
        if meta_name in self.meta['cur']:
            del self.meta['cur'][meta_name]
        self.keydb.remove_role(meta_name)

    def _update_if_changed(self, meta_name, ref_meta_name='release'):
        """Updates the metadata of meta_name if it has changed.
        
        If the metadata needs to be updated but an update cannot be obtained,
        this function will delete the file (with the exception of the root
        metadata, which never gets removed without a replacement).
        
        Raises:
            tuf.MetadataNotAvailableError
            tuf.RepoError
        """
        rel_path = meta_name + '.txt'

        if ref_meta_name not in self.meta['cur']:
            if meta_name == 'root':
                # TODO: how about when release.txt is out of date? Need to make
                # sure the update gets forced. It may not be the code here that
                # needs to change.
                new_file_info = None
            else:
                raise tuf.RepoError("Can't update %s because %s is missing." %
                                    (meta_name, ref_meta_name))
        else:
            new_file_info = self.meta['cur'][ref_meta_name].meta[rel_path]

        if not self._fileinfo_has_changed(rel_path, new_file_info):
            return False

        logger.info("Metadata '%s' has changed" % rel_path)

        compression = None
        if meta_name == 'release':
            gzip_path = rel_path + '.gz'
            if gzip_path in self.meta['cur'][ref_meta_name].meta:
                compression = 'gzip'
        try:
            self._update_metadata(meta_name, compression=compression)
        except tuf.RepoError:
            # The current metadata we have is not current but we couldn't
            # get new metadata. We shouldn't use the old metadata anymore.
            # This will get rid of in-memory knowledge of the role and
            # delegated roles, but will leave delegated metadata files as
            # current files on disk.
            # TODO: Should we get rid of the delegated metadata files?
            # We shouldn't need to, but we need to check the trust
            # implications of the current implementation.
            self._delete_metadata(meta_name)
            msg = "Metadata for %s could not be downloaded." % meta_name
            raise tuf.MetadataNotAvailableError(msg)

        # We need to remove delegated roles because the delegated roles
        # may not be trusted anymore.
        if meta_name == 'targets' or meta_name.startswith('targets/'):
            logger.debug("Removing delegated roles of %s" % meta_name)
            self.keydb.remove_delegated_roles(meta_name)
            self._import_delegations(meta_name)

        return True

    def _ensure_not_expired(self, meta_name):
        """Raise an exception if current specified metadata has expired.
        
        Raises:
            tuf.ExpiredMetadataError
        """
        expires = self.meta['cur'][meta_name].expires
        if expires < time.time():
            exp_formatted = tuf.formats.format_time(expires)
            # TODO: This error is a little confusing in that it can say
            # "Metadata Timestamp has expired on X." This is an argument for
            # using the rel_path here instead of the meta_type.
            msg = "Metadata %s expired on %s." % (meta_name, exp_formatted)
            raise tuf.ExpiredMetadataError(msg)

    def _import_delegations(self, parent_role):
        """
        
        Raises:
            Any unexpected exception that comes from keydb.add_key.
                TODO: Change this or document it better. 
        """
        logger.debug("Adding roles delegated from: %s" % parent_role)
        # This could be quite slow with a huge number of delegations.
        cur_parent_meta = self.meta['cur'][parent_role]
        keys_meta = cur_parent_meta.delegations.get('keys', {})
        roles_meta = cur_parent_meta.delegations.get('roles', {})

        for keyid, keymeta in keys_meta.items():
            key = tuf.keys.RSAKey.from_meta(keymeta)
            # We specify the keyid to ensure that it's the correct keyid
            # for the key.
            #logger.debug("Adding key: %s" % keyid)
            try:
                self.keydb.add_key(key, keyid)
            except tuf.KeyAlreadyExistsError:
                pass
            except Exception:
                logger.exception("Failed to add keyid: %s" % keyid)
                logger.error("Aborting role delegation for parent role: %s" %
                             parent_role)
                raise

        for rolename, roleinfo in roles_meta.items():
            logger.debug("Adding delegated role: %s" % rolename)
            try:
                self.keydb.add_role(rolename, roleinfo)
            except Exception:
                logger.exception("Failed to add delegated role: %s" % rolename)

    def refresh(self):
        """Retrieves the latest copies of the minimal required metadata.
        
        This will result in any "get_target*" functions being able to obtain
        the latest available content.
        
        Raises:
            tuf.RepoError: If any metadata could not be updated.
        """
        # TODO: Should we always try to update root.txt if it has insufficient
        # trusted signatures and there are untrusted signatures?
        self._update_metadata('timestamp')

        self._update_if_changed('release', ref_meta_name='timestamp')

        self._update_if_changed('root')

        self._update_if_changed('targets')

        for meta_name in ['timestamp', 'root', 'release', 'targets']:
            self._ensure_not_expired(meta_name)

    def _refresh_targets_meta(self, rolename='targets',
                              include_delegations=False):
        roles_to_update = []

        # See if this role provides metadata and, if we're including
        # delegations, look for metadata from delegated roles.
        role_prefix = rolename + '/'
        for meta_path in self.meta['cur']['release'].meta.keys():
            #logger.debug("meta: %s" % meta_path)
            if meta_path == rolename + '.txt':
                roles_to_update.append(meta_path[:-len('.txt')])
            elif include_delegations and meta_path.startswith(role_prefix):
                roles_to_update.append(meta_path[:-len('.txt')])

        # Include all parent roles.
        roles_set = set(roles_to_update)
        for rolename in roles_to_update:
            for parent_role in tuf.keydb.get_all_parent_roles(rolename):
                if parent_role not in roles_set:
                    roles_set.add(parent_role)

        # If there's nothing to refresh, we're done.
        if not roles_set:
            return

        # Remove 'targets' because this gets updated with refresh_minimal().
        try:
            roles_set.remove(u'targets')
        except KeyError:
            raise tuf.Error("'targets' not in roles_set of %s (%s) (%s) ?" %
                            (rolename, tuf.keydb.get_all_parent_roles(rolename),
                             roles_set))
        roles_to_update = list(roles_set)

        # Sort the roles so that parent roles always come first.
        roles_to_update.sort()
        logger.debug("Roles to update: %s" % roles_to_update)

        for rolename in roles_to_update:
            self._load_metadata_from_file('prev', rolename)
            self._load_metadata_from_file('cur', rolename)

            self._update_if_changed(rolename)

            try:
                self._ensure_not_expired(rolename)
            except tuf.ExpiredMetadataError:
                self.keydb.remove_role(rolename)

    def get_target(self, target_path):
        """Returns a target object for the target at the specified path.
        
        To get all targets at a specific path, use get_targets_by_path without
        using any file or directory wildcards.
        
        Args:
            target_path: The path to the target file on the repository. This
              will be relative to the 'targets' (or equivalent) direrectory
              on a given mirror.

        Raises:
            tuf.Error: If there is more than one target at the path.
        """
        targets = self.get_targets_matching_path(target_path)
        if len(targets) > 1:
            # TODO: More specific error.
            # TODO: What if the targets are exactly the same? Is that still
            # an error?
            raise tuf.Error("More than one target matches")
        elif len(targets) == 0:
            # TODO: More specific error.
            raise tuf.Error("No targets match")
        else:
            return targets[0]

    def get_targets_matching_path(self, path_pattern):
        """Returns a list of trusted targets that match path_pattern.

        This may be a very slow operation if there is a large amount of
        delegation and many metadata files aren't already downloaded or if
        there are a large number of targets.
        
        Args:
            path_pattern: The pattern that all returned targets should match.
                This will be relative to the 'targets' (or equivalent)
                direrectory on a given mirror.        

        Raises:
            TODO
        """
        targets = self.get_all_targets()
        # TODO: Look at all metadata and for any target path that is allowed
        # to be specified in that metadata which matches path_pattern, include
        # it in the list of targets to be returned.
        raise NotImplementedError

    def get_targets_of_role(self, rolename='targets'):
        """Returns a list of trusted targets directly specified by rolename.
        
        This may be a very slow operation if there is a large amount of
        delegation and many metadata files aren't already downloaded.

        Args:
            rolename: The name of the role whose list of targets are wanted.
            The name of the role should start with 'targets'.
        
        Raises:
            TODO
        """
        self._refresh_targets_meta(rolename)
        return self._get_targets_of_role(rolename, skip_refresh=True)

    def _get_targets_of_role(self, rolename, targets=None, skip_refresh=False):
        if targets is None:
            targets = []

        logger.debug("getting targets of %s" % rolename)

        if not self.keydb.role_exists(rolename):
            raise tuf.UnknownRoleError(rolename)

        # We don't need to worry about the target paths being trusted because
        # this is enforced before any new metadata is accepted.
        if not skip_refresh:
            self._refresh_targets_meta(rolename)
        if self.meta['cur'].get(rolename) is None:
            # TODO: Allow control over whether an error is raised here.
            # For now, just raising a warning.
            msg = "No metadata for %s. Unable to determine targets." % rolename
            warnings.warn(msg, tuf.Warning)
            return targets

        if rolename not in self.meta['cur']:
            return targets

        # First, get the targets specified by the role itself.
        for path, fileinfo in self.meta['cur'][rolename].targets.items():
            targ = Target(self, path, fileinfo)
            if targ not in targets:
                targets.append(targ)

        # Next, get the targets specified by delegated roles.
        for d_role in self.keydb.get_delegated_role_names(rolename):
            self._get_targets_of_role(d_role, targets, skip_refresh)

        return targets

    def get_all_targets(self):
        """Get a list of all trusted targets on the repository.
        
        Raises:
            TODO
        """
        self._refresh_targets_meta(include_delegations=True)
        return self.get_targets_of_role()

    def get_files_to_update(self, targets):
        files_to_update = []
        for target in targets:
            target.path = os.path.sep.join(target.path.split(os.path.sep)[1:])
            path = target.path
            for hash_, digest in target.fileinfo['hashes'].items():
                local_hasher = tuf.hash.Digest(hash_)
                try: local_hasher.update_filename(path)
                except IOError: files_to_update.append(target)
                if local_hasher.format() != digest:
                    files_to_update.append(target)
        return files_to_update


class Target(object):
    """Represents a trusted target described in target metadata."""

    def __init__(self, repo, path, fileinfo):
        self.repo = repo
        self.path = path
        self.fileinfo = fileinfo

    def __repr__(self):
        return ("<Target '%s' from repository '%s'>" % (self.path, self.repo))

    def __str__(self):
        return "'%s' from repository '%s'" % (self.path, self.repo)

    def __eq__(self, other):
        return (self.repo == other.repo and
                self.path == other.path and
                self.fileinfo == other.fileinfo)

    def __ne__(self, other):
        return not self.__eq__(other)

    def download(self, dest_filename):
        """Download the target and verify it's trusted.
        
        This will only store the file at dest_filename if the downloaded
        file matches the description of the file in the trusted metadata.
        
        Args:
            dest_filename:
        
        Raises:
            TODO
        """
        last_err = None

        for job in self.repo.download_job_generator(
            'target', self.path, self.repo.mirrors,
            wantHashes=self.fileinfo['hashes'],
            wantLength=self.fileinfo['length']):
            try:
                temp_file_obj = job.download()
                temp_file_obj.move(dest_filename)
                # Returning the successful job allows getting additional info
                # about the successful download, if desired.
                return job
            # TODO: what other exceptions are there?
            except tuf.DownloadError, err:
                last_err = err
                logger.warn("Download failed from %s: %s" % (job.url, err))
        else:
            if last_err is None:
                raise tuf.DownloadError("No download locations known.")
            else:
                raise last_err
