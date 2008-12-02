#XML-RPC Server

# Configure below
LISTEN_HOST = '127.0.0.1' # You should not use '' here, unless you have a real FQDN.
LISTEN_PORT = 8000

# Paths
PREFIX = "/var/www/remote_installer";
INSTALLER_SCRIPT = PREFIX + "/customize_installers.py";
VESSEL_INFO = PREFIX + "/writecustominstallerinfo.py";

import os
import SimpleXMLRPCServer

# importng Justin's code
# import Carter's code
# import ... as vesselinfopy

class generateInstaller:
    def __init__(self):
        # Make all of the Python string functions available through
        # python_string.func_name
        import string
        self.python_string = string

    def createInstaller(self):
	# vesselinfopy.generate(..)
#		os.system("python $vesselinfopy $dl_prefix/vesselsinfo.txt $dl_prefix/vesselsinfo/");
#       os.system("cd $dl_prefix/tmp/ && python $carter_script mlw $dl_prefix/vesselsinfo $dl_prefix/ > /tmp/carter.out.php 2> /tmp/carter.err.php");		
#		os.system("zip -j $dl_prefix/private.zip $dl_prefix/*.privatekey");
#		os.system("zip -j $dl_prefix/public.zip $dl_prefix/*.publickey");
#       os.system("cp $dl_prefix/seattle_linux.tgz $dl_prefix/seattle_mac.tgz");


	def create_installer(self, vessels):
		""""
		arguments:
			vessels of form [(percent1, owner1, [u1, u2, ...]), (perent2, owner2, u1', u2',...),...]
			where percent is ..
			owner is
			u is ..
	
		"""
		for (percent, owner, users) in vessels:
			owner_key = owner
			user_keys = users
			for u in users
				u_key = users[u]
			
    
server = SimpleXMLRPCServer.SimpleXMLRPCServer((LISTEN_HOST, LISTEN_PORT))
server.register_instance(generateInstaller())
server.serve_forever()

