"""
Author: Xuanhua Ren

Module: Create the customized installer through XML_RPC

Start date: November 28th, 2008


"""


#XML-RPC Server

# Configure below
LISTEN_HOST = '127.0.0.1' # You should not use '' here, unless you have a real FQDN.
LISTEN_PORT = 8000

# Paths
PREFIX = "./";
DOWNLOAD_PREFIX = "downloads/"
INSTALLER_SCRIPT = PREFIX + "customize_installers.py";
VESSELINFO_SCRIPT = PREFIX + "writecustominstallerinfo.py";

import os
import SimpleXMLRPCServer
import re
import customized_installers
import writecustominstaller


# importng Justin's code
# import Carter's code
# import ... as vesselinfopy

class generateInstaller:
    def __init__(self):
        # Make all of the Python string functions available through
        # python_string.func_name
        import string
        self.python_string = string

	def standarize_name(self, username):
		"""
		arguments:
			username that may contain white spaces or uppercase letters
		return:
			username with all lowercase and separated by underscores
		"""
		return re.sub("\s+", "_", string.lower(username))


	def output_vessel_info(self, vessels):
		"""
		arguments:
			vessels of form [(percent1, owner1, [u1, u2, ...]), (perent2, owner2, u1', u2',...),...]
			where percent is the percent of each vessel..
			owner is the owner of each vessel
			u's are the users of each vessel
		return:
			output in format of 
				Percent xxx
				Owner xxx
				User xxx
				User xxx
				...
		"""
		output = "";
		for (percent, owner, users) in vessels:
			output += "Percent " + percent + "\n"
			output += "Owner " + owner + "\n"	
			for u in users
				output += "User " + u + "\n"
 		return output




        exec("cd $dl_prefix/tmp/ && python $carter_script mlw $dl_prefix/vesselsinfo $dl_prefix/ > /tmp/carter.out.php 2> /tmp/carter.err.php");
				

	def create_installer(self, vessels):
		""""
		arguments:
			vessels of form [(percent1, owner1, [u1, u2, ...]), (perent2, owner2, u1', u2',...),...]
			where percent is the percent of each vessel..
			owner is the owner of each vessel
			u's are the users of each vessel
	
		"""
		f = open(DOWNLOAD_PREFIX + 'vesselinfo.txt', 'w')
		f.write(output_vessel_info)
		f.close()
		
    	VESSELINFO_SCRIPT.create_installer_state("vesselinfo.txt", DOWNLOAD_PREFIX)
		
		
		# os.system("cp $dl_prefix/seattle_linux.tgz $dl_prefix/seattle_mac.tgz");




server = SimpleXMLRPCServer.SimpleXMLRPCServer((LISTEN_HOST, LISTEN_PORT))
server.register_instance(generateInstaller())
server.serve_forever()

