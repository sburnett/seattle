"""
<Program Name>
  import_keys.py

<Started>
  March 27, 2008

<Author>
  ivan@cs.washington.edu
  Ivan Beschastnikh

<Purpose>
  Imports keys from files into the geni db.

<Usage>
  This script is best run as geni@seattlegeni as t requires django, and
  mysql settings to be available in its path. The geni user has these
  by default.

  Run from the command line with glob expression for **publickeys** to
  import as an argment:
  $ python dbnode_checker.py './*cs.washington.edu*publickey*'

  NOTE: Make sure to enclose the glob expression into single quotes so
  that it is not evaluated by the shell before being passed to the
  python script!

  NOTE: privatekeys are assume to have the same filename as
  publickeys, except for the ending (privatekey instead of publickey).
"""

import sys
import glob
import repyhelper
import time

from django.db import connection

repyhelper.translate_and_import("rsa.repy")

def import_key(pubkeyfn):
    """
    <Purpose>
        Import a publickey located in pubkeyfn file, and the
        corresponding privatekey in the geni db.

    <Arguments>
        pubkeyfn : filename of publickey

    <Exceptions>
        None.

    <Side Effects>
        Adds a new record to the keygen database

    <Returns>
        None
    """
    pubkey = rsa_file_to_publickey(pubkeyfn)
    privkeyfn = pubkeyfn.replace("publickey", "privatekey")
    privkey = rsa_file_to_privatekey(privkeyfn)

    pubkeystr = rsa_publickey_to_string(pubkey)
    privkeystr = rsa_privatekey_to_string(privkey)

    print time.ctime(), "pubkey is", pubkeystr
    print time.ctime(), "privkey is", privkeystr
    
    insert_statement = 'INSERT INTO keygen.keys_512 (pub,priv) values ("%s", "%s")'%(pubkeystr, privkeystr)
    # print "insert statement is :\n", insert_statement

    cursor = connection.cursor()
    try:
        cursor.execute("BEGIN")
        cursor.execute(insert_statement)
    except Exception, e:
        print "INSERT raised Exception: ", e
        cursor.execute("ABORT")
    else:
        cursor.execute("COMMIT")
    return



if __name__ == "__main__":
    if len(sys.argv) != 2:
        print "usage: %s [publickey_glob_expression]"%(sys.argv[0])
        sys.exit(1)
        
    pubkeysfns = glob.glob(sys.argv[1])
    for pubkeyfn in pubkeysfns:
        print "importing pubkey", pubkeyfn
        import_key(pubkeyfn)

    
    
