# Copyright 2010 The Update Framework.  See LICENSE for licensing information.

import urllib

import tuf.download


MIRROR_BASE_URL = "/home/justin/workspace/updater"


def mirror_download_job_generator(file_type, path, mirrors,
                                  wantHashes=None, wantLength=None):
    """Generator: yields all download jobs possible to download a file
       from the mirrors."""
    for m_name, m_info in mirrors.items():
        if file_type is 'meta':
            if not tuf.util.path_in_patterns(path, m_info['metacontent']):
                continue
            base = "%s/%s" % (m_info['urlbase'], m_info['metapath'])

        elif file_type in ['target', 'targets']:
            if not tuf.util.path_in_patterns(path, m_info['targetscontent']):
                continue
            base = "%s/%s" % (m_info['urlbase'], m_info['targetspath'])

        else:
            raise tuf.Error("Unknown file type: %s" % file_type)

        path = urllib.quote(path)
        url = "%s/%s" % (base, path)
        yield tuf.download.DownloadJob(url, wantHashes=wantHashes,
                                       wantLength=wantLength)
