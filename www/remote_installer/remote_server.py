"""
<Program Name>
	remote_server.py

<Started>
	November 28th, 2008

<Author>
	shawiz@cs.washington.edu
	Xuanhua Ren (Sean)

<Purpose>
	Provide remote methods to build customized installer on server side
	through XML-RPC.
	
	The methods are core functions to build the customized installer for
	the user, and it will eventually the urls for the customized built
	installers

"""


# todos: make external calls into importing

import sys
import os
import re
import SimpleXMLRPCServer

# importng Justin's code
# import Carter's code
# import ... as vesselinfopy

class generateInstaller:
	"""
	<Purpose>
		Class to generate the installer
	<Example Use>
		# create gen installer instance
		gen_installer = generateInstaller(prefix, dl_prefix)
		# build the installer and get its url
		url = server.build_installer(user_key_dict, vessel_info)
	"""
	
	def __init__(self, prefix, dl_prefix):
		"""
		<Purpose>
			Initialize the instance
		<Arguments>
			prefix:
				the system prefix of current directory
			dl_prefix:
				prefix of download folder
	   """
		self.prefix = prefix
		self.dl_prefix = self.prefix + "/" + dl_prefix
		self.installer_script = self.prefix + "/customize_installers.py"
		self.vesselinfo_script = self.prefix + "/writecustominstallerinfo.py"


	# def standarize_name(self, username):
	#	 """
	#	arguments:
	#		username that may contain white spaces or uppercase letters
	#	return:
	#		username with all lowercase and separated by underscores
	#	"""
	#	return re.sub("\s+", "_", string.lower(username))
   

	def output_vessel_info(self, user_key_dict, vessels):
		"""
		<Purpose>
			Output the vessel information in a specific format
		<Arguments>
			user_key_dict:
				dictionary of form {"username1": "key1", "username2": "key2", ...}
			vessels:
				vessels of form [user_key_dict, (percent1, owner1, [u1, u2, ...]),
				(perent2, owner2, u1', u2',...),...]
				where user_key_dict is a dictionar mapping usernames to public keys
				percent is the percent of each vessel..
				owner is the owner username of each vessel
				u's are the usernames corresponding to users of each vessel
		<Returns>
			output string in format of 
				Percent xxx
				Owner xxx
				User xxx
				User xxx
				...
		"""

		output = ""
		for (percent, owner, users) in vessels:
			output += "Percent " + str(percent) + "\n"
			output += "Owner " + user_key_dict[owner] + "\n"	   
			for u in users:
				output += "User " + user_key_dict[u] + "\n"
		return output


	def build_installer(self, user_key_dict, vessels):
		"""
		<Purpose>
			Create the customized installer by taking the user-key pair and
			vessel info
				
		<Arguments>
			user_key_dict:
				the dictionary containing the user - public key pair
				see method above for detailed format
			vessels:
				the vessel information given by the user
				see method above for detailed format
			
		<Returns>
			The url of the installer it builds
		"""
		
		# a dummy username for testing (needs to be removed)
		username = "foo"
		# a dummy dist_char for testing (needs to be removed)
		dist_char = "m"
		
		# prefix dir is specific to this user
		user_prefix = self.prefix + "/%s_dist"%(username)

		# remove and recreate the prefix dir
		os.system("rm -Rf %s/"%(user_prefix))
		os.system("mkdir %s/"%(user_prefix))

		# write out to file the user's donor key
		# f = open('%s/%s'%(user_prefix, username),'w');
		# f.write("%s"%(username.donor_pubkey))
		# f.close()

		# write out to file the geni lookup key
		# f = open('%s/%s_geni'%(user_prefix, username),'w');
		# f.write("%s"%(genilookuppubkey))
		# f.close()

		# write out to file the vesselinfo to customize the installer
		vessel_info = self.output_vessel_info(user_key_dict, vessels)
		f = open('%s/vesselinfo'%(user_prefix),'w');
		f.write("%s"%(vessel_info))
		f.close()

		# create the dir where vesselinfo will be created
		os.system("mkdir %s/vesselinfodir/"%(self.prefix))
		
		# create the vessel info
		cmd = "cd %s && python %s %s/vesselinfo %s/vesselinfodir 2> /tmp/customize.err > /tmp/customize.out"%(self.prefix, self.vesselinfo_script, user_prefix, self.prefix)
		#f = open("/tmp/out", "w")
		#f.write(cmd)
		os.system(cmd)
		
		# run carter's script to create the installer of the particular type ((w)in, (l)inux, or (m)ac)
		os.system("python %s %s %s/vesselinfodir/ %s/ > /tmp/installer.out 2> /tmp/installer.err"%(self.installer_script, dist_char, self.prefix, self.prefix))
		#os.system("python %s %s %s/vesselinfodir/ %s/ &> /tmp/out"%(carter_script, dist_char, prefix,prefix))
		
		# compose and return the url to which the user needs to be redirected
		return "http://seattle.cs.washington.edu/dist/geni/%s_dist/"%(username)	   





if __name__ == "__main__":

	if len(sys.argv) < 4:
		print "usage: python remote_server.py hostname port download_prefix"
	else:
		host = sys.argv[1]
		port = sys.argv[2]
		dl_prefix = sys.argv[3]

	# default arguments for testing purpose
	host = '127.0.0.1'
	port = 8000
	prefix = "/Users/shawiz/Development/research/www/remote_installer"
	dl_prefix = "download"
	
	
	# create the XMLRPC server
	server = SimpleXMLRPCServer.SimpleXMLRPCServer((host, port))
	# create gen installer instance
	gen_installer = generateInstaller(prefix, dl_prefix)
	# serve the gen_installer instance via the server
	server.register_instance(gen_installer)
	# begin the serving loop
	server.serve_forever()
