"""
Author: Xuanhua Ren

Module: Create the customized installer through XML_RPC

Start date: November 28th, 2008


"""



#todos: make external calls into importing
#XML-RPC Server

import os
import re
import SimpleXMLRPCServer

# importng Justin's code
# import Carter's code
# import ... as vesselinfopy

class generateInstaller:
    def __init__(self, prefix, dl_prefix):
		self.prefix = prefix
		self.dl_prefix = self.prefix + "/" + dl_prefix
		self.installer_script = self.prefix + "customize_installers.py";
		self.vesselinfo_script = self.prefix + "writecustominstallerinfo.py";

	def standarize_name(self, username):
		"""
		arguments:
			username that may contain white spaces or uppercase letters
		return:
			username with all lowercase and separated by underscores
		"""
		return re.sub("\s+", "_", string.lower(username))


	def output_vessel_info(self, user_key_dict, vessels):
		"""
		arguments:
			vessels of form [user_key_dict, (percent1, owner1, [u1, u2, ...]), (perent2, owner2, u1', u2',...),...]
			where user_key_dict is a dictionar mapping usernames to public keys
			percent is the percent of each vessel..
			owner is the owner username of each vessel
			u's are the usernames corresponding to users of each vessel
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
			output += "Owner " + user_key_dict[owner] + "\n"	
			for u in users
				output += "User " + user_key_dict[u] + "\n"
 		return output


	def build_installer(username, dist_char):
	    '''
	    returns url to the finished installer
	    dist_char is in "lwm"
	    '''

	    # prefix dir is specific to this user		
	    user_prefix = self.prefix + "/%s_dist"%(username)
	    
		# remove and recreate the prefix dir
	    os.system("rm -Rf %s/"%(usr_prefix))
	    os.system("mkdir %s/"%(usr_prefix))

	    # write out to file the user's donor key
	    f = open('%s/%s'%(usr_prefix, username),'w');
	    f.write("%s"%(geni_user.donor_pubkey))
	    f.close()

	    # write out to file the geni lookup key
	    f = open('%s/%s_geni'%(usr_prefix, username),'w');
	    f.write("%s"%(genilookuppubkey))
	    f.close()


	    # write out to file the vesselinfo to customize the installer
	    vesselinfo = '''Percent 8\nOwner %s/%s\nUser %s/%s_geni\n'''%(usr_prefix, username, usr_prefix, username);
	    f = open('%s/vesselinfo'%(usr_prefix),'w');
	    f.write("%s"%(vesselinfo))
	    f.close()

		
	    vesselinfo_script = prefix + "writecustominstallerinfo.py"
	    installer_script = prefix + "customize_installers.py"

	    # create the dir where vesselinfo will be created
	    os.system("mkdir %s/vesselinfodir/"%(prefix))
	    # create the vessel info
	    cmd = "cd %s && python %s %s/vesselinfo %s/vesselinfodir 2> /tmp/customize.err > /tmp/customize.out"%(prefix, vesselinfo_script, prefix, prefix)
	    #f = open("/tmp/out", "w")
	    #f.write(cmd)
	    os.system(cmd)
	    # run carter's script to create the installer of the particular type ((w)in, (l)inux, or (m)ac)
	    os.system("python %s %s %s/vesselinfodir/ %s/ > /tmp/installer.out 2> /tmp/installer.err"%(installer_script, dist_char, prefix, prefix))
	    #os.system("python %s %s %s/vesselinfodir/ %s/ &> /tmp/out"%(carter_script, dist_char, prefix,prefix))
	    # compose and return the url to which the user needs to be redirected
	    # redir_url = "http://seattle.cs.washington.edu/dist/geni/%s_dist/"%(username)
	    return True


if __name__ == "__main__":

	# get args from user here
	
	host = '127.0.0.1'	# You should not use '' here, unless you have a real FQDN.
	port = 8000
	prefix = "/Users/shawiz/Development/research/www/remote_installer"
	dl = "download"
	
	# create the XMLRPC server
	server = SimpleXMLRPCServer.SimpleXMLRPCServer((host, port))
	# create gen installer instance
	gen_installer = generateInstaller(prefix, dl_prefix)
	# serve the gen_installer instance via the server
	server.register_instance(gen_installer)
	# begin the serving loop
	server.serve_forever()

