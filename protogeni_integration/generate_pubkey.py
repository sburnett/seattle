import sys

# Edit the next line to put the correct path where the seattle library
# files are located.
sys.path.append("/path/to/seattle/library")

import repyhelper
repyhelper.translate_and_import('rsa.repy')

print rsa_publickey_to_string(rsa_gen_pubpriv_keys(1024)[0])
