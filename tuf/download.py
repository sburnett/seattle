# Copyright 2008 The Tor Project, Inc.  See LICENSE for licensing information.
# Copyright 2010 The Update Framework.  See LICENSE for licensing information.

import httplib
import sys
import urllib2

import tuf.hash
import tuf.log
import tuf.util

logger = tuf.log.get_logger()


class BaseDownloadJob(object):
    """Abstract base class.  Represents a thing to be downloaded, and the
       knowledge of how to download it."""

    url = None

    # Meta-information, such as headers for HTTP requests.
    info = None

    def download(self):
        raise NotImplementedError


class DownloadJob(BaseDownloadJob):
    """A download job that supports urls supported by urllib2."""

    def __init__(self, url, wantHashes=None, wantLength=None):
        """Create a new DownloadJob.  When it is finally downloaded,
           store it in targetPath.  Store partial results in tmpPath;
           if there is already a file in tmpPath, assume that it is an
           incomplete download. If wantHashes, reject the file unless
           the hash is as given.  If useTor, use a socks connection.
           If repoFile, use that RepositoryFile to validate the downloaded
           data.
           
           targetPath can be None if baseUrl is the full url of the file to be
           downloaded.
           """
        self.url = url
        self._wantHashes = wantHashes
        self._wantLength = wantLength
        self._temp_file_obj = None

    def download(self):
        """Downloads the file, blocking until download is complete.
        
        Returns:
            A tuf.util.TempFile instance where the downloaded data is stored.
           
        Raises:
            tuf.DownloadError: If any error occurred that prevented the
                download or storage of the file from being successful.
        """
        try:
            self._download()
            return self._temp_file_obj
        except (urllib2.HTTPError, tuf.DownloadError), err:
            # TODO: document which types of situations cause each error.
            # urllib2.HTTPError can be caused by 404.
            raise tuf.DownloadError(err)
        except (OSError, httplib.error, IOError, urllib2.URLError), err:
            # Could be the mirror; could be the network.  Hard to say.
            raise tuf.DownloadError(err)
        except:
            err = sys.exc_info()[1]
            logger.exception(err)
            raise tuf.DownloadError(err)

    def _check_hash(self):
        """Helper: check whether the downloaded temporary file matches
           the hash and/or format we need."""
        if self._wantHashes is None:
            return
        for algorithm, expected in self._wantHashes.items():
            digest_obj = tuf.hash.Digest(algorithm)
            digest_obj.update(self._temp_file_obj.read())
            actual = digest_obj.format()
            if actual != expected:
                raise tuf.BadHash("Expected %s, got %s." % (expected, actual))
            else:
                logger.info("Correct hash: %s" % expected)

    def _download(self):
        # Implementation function.  Unlike download(), can throw exceptions.
        self._temp_file_obj = tuf.util.TempFile()
        f_in = None

        try:
            url = self.url.replace("\\", "/")
            logger.info("Downloading %s", url)
            f_in = open_url(url)
            logger.debug("Connected to %s", url)

            self.info = f_in.info()

            expectLength = f_in.info().get("Content-Length", "???")

            # TODO: if expectLength is too large, we don't even need to
            # continue.

            total = 0
            while True:
                c = f_in.read(min(8192, int(expectLength) - total))
                if not c:
                    logger.debug("Got %s/%s bytes from %s", total,
                                 expectLength, url)
                    break
                self._temp_file_obj.write(c, auto_flush=False)
                total += len(c)
                if self._wantLength != None and total > self._wantLength:
                    msg = ("Read too many bytes from %s; got %s, but "
                           "wanted %s" % (url, total, self._wantLength))
                    logger.warn(msg)
                    raise tuf.DownloadError(msg)

            if self._wantLength != None and total != self._wantLength:
                logger.warn("Length wrong on file %s", url)
                raise tuf.DownloadError("Wrong length. Expected %s, got %s" %
                                        (self._wantLength, total))
        finally:
            if f_in is not None:
                f_in.close()
            self._temp_file_obj.flush()

        try:
            self._check_hash()
        except tuf.FormatException:
            self._temp_file_obj.delete()
            raise


def open_url(url):
    """Open a connection to 'url'. This supports the schemes that urllib does,
       which are http:, ftp:, and file:. It will also support https: if python
       has the ssl module available (Python 2.6+)."""
    # TODO: Do proper ssl cert/name checking.
    # TODO: Disallow SSLv2.
    # TODO: Support ssl with MCrypto.
    # TODO: Determine whether this follows http redirects and decide if we like
    # that. For example, would we not want to allow redirection from ssl to
    # non-ssl urls?
    req = urllib2.Request(url)
    conn = urllib2.urlopen(req)
    return conn

if __name__ == '__main__':
    # Trivial CLI to test out downloading.

    import getopt
    options, args = getopt.getopt(sys.argv[1:], "")

    url = args[0]

    job = DownloadJob(url)
    temp_file_obj = job.download()
    print temp_file_obj.read()
