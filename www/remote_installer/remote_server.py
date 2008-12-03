"""
Author: Xuanhua Ren

Module: Create the customized installer through XML_RPC

Start date: November 28th, 2008


"""


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
		self.dl_prefix = dl_prefix
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
			output += "Owner " + owner + "\n"	
			for u in users
				output += "User " + u + "\n"
 		return output




        exec("cd $dl_prefix/tmp/ && python $carter_script mlw $dl_prefix/vesselsinfo $dl_prefix/ > /tmp/carter.out.php 2> /tmp/carter.err.php");
				

	def build_installer(self, vessels):
		""""
		arguments:
			vessels of form [(percent1, owner1, [u1, u2, ...]), (perent2, owner2, u1', u2',...),...]
			where percent is the percent of each vessel..
			owner is the owner of each vessel
			u's are the users of each vessel
	
		"""
		f = open(dl_prefix + 'vesselinfo.txt', 'w')
		f.write(output_vessel_info)
		f.close()
		
    	vesselinfo_script.create_installer_state("vesselinfo.txt", dl_script)
		
		
		# os.system("cp $dl_prefix/seattle_linux.tgz $dl_prefix/seattle_mac.tgz");

	def build_installer(username, dist_char):
	    '''
	    returns url to the finished installer
	    dist_char is in "lwm"
	    '''

	    # prefix dir is specific to this user
	    prefix = "/var/www/dist/geni/%s_dist"%(username)
	    # remove and recreate the prefix dir
	    os.system("rm -Rf %s/"%(prefix))
	    os.system("mkdir %s/"%(prefix))

	    # write out to file the user's donor key
	    f = open('%s/%s'%(prefix, username),'w');
	    f.write("%s"%(geni_user.donor_pubkey))
	    f.close()

	    # write out to file the geni lookup key
	    f = open('%s/%s_geni'%(prefix, username),'w');
	    f.write("%s"%(genilookuppubkey))
	    f.close()

	    # write out to file the vesselinfo to customize the installer
	    vesselinfo = '''Percent 8\nOwner %s/%s\nUser %s/%s_geni\n'''%(prefix,username,prefix,username);
	    f = open('%s/vesselinfo'%(prefix),'w');
	    f.write("%s"%(vesselinfo))
	    f.close()

	    # paths to custominstallerinfo and carter's customize_installers script
	    vesselinfopy = "/home/ivan/trunk/test/writecustominstallerinfo.py"
	    carter_script = "/home/ivan/trunk/dist/customize_installers.py"

	    # create the dir where vesselinfo will be created
	    os.system("mkdir %s/vesselinfodir/"%(prefix))
	    # create the vessel info
	    cmd = "cd /var/www/dist/geni && python %s %s/vesselinfo %s/vesselinfodir 2> /tmp/customize.err > /tmp/customize.out"%(vesselinfopy, prefix, prefix)
	    #f = open("/tmp/out", "w")
	    #f.write(cmd)
	    os.system(cmd)
	    # run carter's script to create the installer of the particular type ((w)in, (l)inux, or (m)ac)
	    os.system("python %s %s %s/vesselinfodir/ %s/ > /tmp/carter.out 2> /tmp/carter.err"%(carter_script, dist_char, prefix,prefix))
	    #os.system("python %s %s %s/vesselinfodir/ %s/ &> /tmp/out"%(carter_script, dist_char, prefix,prefix))
	    # compose and return the url to which the user needs to be redirected
	    redir_url = "http://seattle.cs.washington.edu/dist/geni/%s_dist/"%(username)
	    return True, redir_url


if __name__ == "__main__":

	# get args from user here
	
	host = '127.0.0.1'	# You should not use '' here, unless you have a real FQDN.
	port = 8000
	prefix = "/Users/shawiz/Development/research/www/remote_installer/"
	dl_prefix = prefix + "downloads/"
	
	
	
	# create the XMLRPC server
	server = SimpleXMLRPCServer.SimpleXMLRPCServer((host, port))
	# create gen installer instance
	gen_installer = generateInstaller(prefix, dl_prefix)
	# serve the gen_installer instance via the server
	server.register_instance(gen_installer)
	# begin the serving loop
	server.serve_forever()

