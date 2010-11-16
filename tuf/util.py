# Copyright 2008 The Tor Project, Inc.  See LICENSE for licensing information.
# Copyright 2010 The Update Framework.  See LICENSE for licensing information.

import gzip
import os
import re
import shutil
import sys
import tempfile

import tuf.log
import tuf.conf

logger = tuf.log.get_logger()

_json_module = None


def import_json():
    global _json_module
    if _json_module is not None:
        return _json_module

    for name in [ "json", "simplejson" ]:
        try:
            mod = __import__(name)
        except ImportError:
            continue
        if not hasattr(mod, "dumps"):
            # Some versions of Ubuntu have a module called 'json' that is
            # not a recognizable simplejson module.  Naughty.
            if name == 'json':
                logger.warn("Your operating system has a nonfunctional json "
                            "module.  That's going to break any programs that "
                            "use the real json module in Python 2.6.  Trying "
                            "simplejson instead.")
            continue

        # Some old versions of simplejson escape / as \/ in a misguided and
        # inadequate attempt to fix XSS attacks.  Make them not do that.  This
        # code is not guaranteed to work on all broken versions of simplejson:
        # it replaces an entry in the internal character-replacement
        # dictionary so that "/" is translated to itself rather than to \/.
        # We also need to make sure that ensure_ascii is False, so that we
        # do not call the C-optimized string encoder in these broken versions,
        # which we can't fix easily.  Both parts are a kludge.
        try:
            escape_dct = mod.encoder.ESCAPE_DCT
        except NameError:
            pass
        else:
            if escape_dct.has_key("/"):
                escape_dct["/"] = "/"
                save_dumps = mod.dumps
                save_dump = mod.dump
                def dumps(*k, **v):
                    v['ensure_ascii'] = False
                    return save_dumps(*k, **v)
                def dump(*k, **v):
                    v['ensure_ascii'] = False
                    return save_dump(*k, **v)
                mod.dump = dump
                mod.dumps = dumps
                logger.warn("Your operating system has an old broken "
                            "simplejson module.  I tried to fix it for you.")

        _json_module = mod
        return mod

    raise ImportError("Couldn't import a working json module")


json = import_json()


def move_file(fromLocation, toLocation):
    """Move the file from fromLocation to toLocation, removing any file
       in toLocation.
    """
    if sys.platform in ('cygwin', 'win32'):
        # Win32 doesn't let rename replace an existing file.
        try:
            os.unlink(toLocation)
        except OSError:
            pass

    os.rename(fromLocation, toLocation)


def replace_file(fname, contents, textMode=False):
    """overwrite the file in 'fname' atomically with the content of 'contents'
    """
    dir, prefix = os.path.split(fname)
    fd, fname_tmp = tempfile.mkstemp(prefix=prefix, dir=dir, text=textMode)

    try:
        os.write(fd, contents)
    finally:
        os.close(fd)

    move_file(fname_tmp, fname)


def user_filename(name):
    """Return a path relative to $TUF_HOME or ~/.tuf whose final path
       component is 'name', creating parent directories as needed."""
    try:
        base = os.environ["TUF_HOME"]
    except KeyError:
        base = "~/.tuf"

    base = os.path.expanduser(base)
    result = os.path.normpath(os.path.join(base, name))
    ensure_parent_dir(result)
    return result


def get_file_details(filename):
    """Get length and hash information about a file.
    
    Args:
        filename: The path to a file.
        
    Returns:
        A tuple of (length, hashes) describing filename.
    """
    length = os.path.getsize(filename)

    d_obj = tuf.hash.Digest('sha256')
    d_obj.update_filename(filename)

    hashes = {'sha256' : d_obj.format()}
    return length, hashes


class TempFile(object):
    """A high-level temporary file that cleans itself up or can be manually
       cleaned up. This isn't a complete file-like object. The file functions
       that are supported make additional common-case safe assumptions. There
       are additional functions that aren't part of file-like objects."""

    def __init__(self, prefix='tmp'):
        self._compression = None
        self._orig_file = None
        temp_dir = tuf.conf.settings.temp_dir
        if temp_dir is not None:
            # We use TemporaryFile for the auto-delete aspects of it to ensure
            # we don't leave behind temp files.
            try:
                self._file = tempfile.TemporaryFile(prefix=prefix, dir=temp_dir)
            except OSError, err:
                logger.error("Temp file in %s failed: %s " % (temp_dir, err))
                logger.error("Will attempt to use system default temp dir.")

        try:
            self._file = tempfile.TemporaryFile(prefix=prefix)
        except OSError, err:
            logger.critical("Temp file in %s failed: %s " % (temp_dir, err))
            # TODO: raise an exception that indicates an unrecoverable error.

    def delete(self):
        self._file.close()
        # If compression has been set, we need to explicitly close the original
        # file object.
        if self._orig_file is not None:
            self._orig_file.close()

    def flush(self):
        self._file.flush()

    def move(self, dest_path):
        """Copies a temp file at src to a non-temp file at dst and then closes
           the temp file so that it is removed."""
        self.flush()
        self.seek(0)
        f_dst = open(dest_path, 'wb')
        shutil.copyfileobj(self._file, f_dst)
        f_dst.close()
        self.delete()

    def read(self, size=None):
        """If no size specified, read the whole file and leave the file pointer
           at the beginning of the file."""
        if size is None:
            self._file.seek(0)
            data = self._file.read()
            self._file.seek(0)
            return data
        else:
            return self._file.read(size)

    def seek(self, *args):
        self._file.seek(*args)

    def write(self, str, auto_flush=True):
        self._file.write(str)
        if auto_flush:
            self.flush()
            
    def set_compression(self, compression):
        """Basic functionality for dealing with a TempFile that is compressed.
           After calling this, write() can no longer be called."""
        if self._orig_file is not None:
            raise tuf.Error("Can only set compression on a TempFile once.")
        if compression != 'gzip':
            raise tuf.Error("Only gzip compression is supported.")
        self.seek(0)
        self._compression = compression
        self._orig_file = self._file
        self._file = gzip.GzipFile(fileobj=self._file, mode='rb')
    

def load_json_string(data):
    return json.loads(data)


def load_json_file(filename):
    fp = open(filename)
    try:
        return json.load(fp)
    finally:
        fp.close()


def ensure_parent_dir(name):
    """If the parent directory of 'name' does not exist, create it."""
    directory = os.path.split(name)[0]
    if directory and not os.path.exists(directory):
        os.makedirs(directory, 0700)


_path_regex_cache = {}

def path_in_patterns(path, pattern_list):
    """Return true iff the relative path in the filesystem 'path' conforms
       to the pattern 'rolePath': a path that a given key is
       authorized to sign.  Patterns are allowed to contain * to
       represent one or more characters in a filename, and ** to
       represent any level of directory structure.
       
       Part of the reason for making it a pattern list instead of a pattern
       is that we always end up dealing with pattern lists. The other part
       of the reason is that it's nice to force the arguments to be of
       different types to prevent callers mixing the two up and somehow not
       noticing.

    >>> path_in_patterns("a/b/c/", ["a/b/c/"])
    True
    >>> path_in_patterns("**/c.*", ["a/b/c.txt"])
    True
    >>> path_in_patterns("**/c.*", ["a/b/ctxt"])
    False
    >>> path_in_patterns("**/c.*", ["a/b/c.txt/foo"])
    False
    >>> path_in_patterns("a/*/c", ["a/b/c"])
    True
    >>> path_in_patterns("a/*/c", ["a/b/c.txt"])
    False
    >>> path_in_patterns("a/*/c", ["a/b/c.txt"]) #Check cache
    False
    """
    if not isinstance(path, basestring):
        raise TypeError("The path must be a string.")
    if not isinstance(pattern_list, (list, tuple)):
        raise TypeError("The pattern_list must be a list or a tuple.")

    for pattern in pattern_list:
        # Ignore slashes at the beginning.
        pattern = pattern.lstrip('/')
        try:
            regex = _path_regex_cache[pattern]
        except KeyError:
            orig = pattern
            # Remove duplicate slashes.
            pattern = re.sub(r'/+', '/', pattern)
            # Escape, then ** becomes .*
            pattern = re.escape(pattern).replace(r'\*\*', r'.*')
            # * becomes [^/]*
            pattern = pattern.replace(r'\*', r'[^/]*')
            # No extra text is allowed.
            pattern = '^' + pattern + '$'
            regex = _path_regex_cache[orig] = re.compile(pattern)

        if regex.match(path) != None:
            return True

    return False
