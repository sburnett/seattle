import sys
sys.path.append("/home/monzum/monitor_nodes_scripts/seattle")

import repyhelper
repyhelper.translate_and_import('rsa.repy')

print rsa_publickey_to_string(rsa_gen_pubpriv_keys(1024)[0])
