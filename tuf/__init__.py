# Copyright 2008 The Tor Project, Inc.  See LICENSE for licensing information.
# Copyright 2010 The Update Framework.  See LICENSE for licensing information.

__all__ = [ 'formats' ]

# TODO(jsamuel): Make sure these all end in Error except where there is a good
# reason not to, and describe that reason in those cases.

class Error(Exception):
    pass

class Warning(Warning):
    pass

class FormatException(Error):
    pass

class UnsupportedAlgorithmError(Error):
    pass

class UnknownFormat(FormatException):
    pass

class BadHash(Error):
    pass

class BadSignature(Error):
    pass

class BadPassword(Error):
    pass

class UnknownKeyError(Error):
    pass

class InternalError(Error):
    pass

class RepoError(Error):
    pass

class ExpiredMetadataError(Error):
    pass

class MetadataNotAvailableError(Error):
    pass

class CryptoError(Error):
    pass

class PubkeyFormatException(FormatException):
    pass

class UnknownMethod(CryptoError):
    pass

class DownloadError(Error):
    pass

class CheckNotSupported(Error):
    pass

class KeyAlreadyExistsError(Error):
    pass

class RoleAlreadyExistsError(Error):
    pass

class UnknownRoleError(Error):
    pass

class InvalidNameError(Error):
    pass

#class RemoveNotSupported(Error):
#    pass
#
#class InstallFailed(Error):
#    pass
