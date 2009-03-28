"""
<Program Name>
  genkeys.py

<Started>
  March 27, 2008

<Author>
  ivan@cs.washington.edu
  Ivan Beschastnikh

<Purpose>
  Generates keys in parallel.

<Usage>
  This script is intended to run on different machines at the same
  time to quickly generate many public/private keypairs.

  Run from the command line with a single integer argument for the
  number of keys to generate -- this will also be the parallelism
  number (e.g. number of processes that will each generate one
  keypair)
  $ python genkeys.py 100

  This scripts generates key files of the form:
  hostname_X.publickey
  hostname_X.privatekey
  Where X is an integer

  NOTE: you'll need to modify generatekeys_path below to point to the
  generatekeys.py script that does the keypair generation
"""

import os
import sys

# modify this to be the path of the generatekeys script
generatekeys_path = '/homes/network/ivan/generatekeys.py'


def main(parallelism):
  """
  <Purpose>
    Spawns parallelism number of processes to generate a keypair each.

  <Arguments>
    parallelism : number of processes to spawn

  <Exceptions>
    None.

  <Side Effects>
    Creates processes and keypair files.

  <Returns>
    None
  """
  for i in range(parallelism):
    if not os.fork():
      os.system("python %s `hostname`_%d 512"%(generatekeys_path, i))
      sys.exit(1)

  # now we wait for the children we've spawned
  for i in range(parallelism):
    os.wait()
  return



if __name__ == "__main__":
  if len(sys.argv) != 2:
    print "usage: %s [parallelism]"%(sys.argv[0])
    sys.exit(1)
        
  parallelism = int(sys.argv[1])
  main(parallelism)

