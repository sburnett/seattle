"""
<Program Name>
	remote_client.py

<Started>
	November 28th, 2008

<Author>
	shawiz@cs.washington.edu
	Xuanhua Ren (Sean)

<Purpose>
	Client that calls the remote build installer function to create
	customized installer
"""

import xmlrpclib

def __genkey__(username):
	"""
	<Purpose>
		Internal method to generate keys for users
	<Arguments>
		username:
			the user who we want to generate key for
	<Returns>
		the key for the user
	"""
	
	# write keys to the file
	os.system("python generatekeys.py %s %s %s"%(username, 20, "keys"))
	
	# read the public key from file
	f = open("/keys/%s.public"%(username), 'r')
	key = f.read()
	f.close()
	
	return key


def create_installer_with_keys(user_key_dict, vessel_info, dist_str):
	"""
	<Purpose>
		Create the installe with given user-key pairs and vessel info
	<Arguments>
		user_key_dict:
			dictionary of form {"username1": "key1", "username2": "key2", ...}
		vessel_info:
			vessels of form [user_key_dict, (percent1, owner1, [u1, u2, ...]),
			(perent2, owner2, u1', u2',...),...]
			where user_key_dict is a dictionar mapping usernames to public keys
			percent is the percent of each vessel..
			owner is the owner username of each vessel
			u's are the usernames corresponding to users of each vessel
		dist_str:
			string that contains any combination of letter w (Windows),
			l (Linux), or m (Mac). example "lm"
	<Returns>
		the url for the installer
	"""

	server = xmlrpclib.Server('http://localhost:8000')
	return server.build_installer(user_key_dict, vessel_info, dist_str)
	

def create_installer_without_keys(vessel_info, dist_str):
	"""
	<Purpose>
		Create the installe with vessel info only
	<Arguments>
		vessel_info:
			vessels of form [user_key_dict, (percent1, owner1, [u1, u2, ...]),
			(perent2, owner2, u1', u2',...),...]
			where user_key_dict is a dictionar mapping usernames to public keys
			percent is the percent of each vessel..
			owner is the owner username of each vessel
			u's are the usernames corresponding to users of each vessel
		dist_str:
			string that contains any combination of letter w (Windows),
			l (Linux), or m (Mac). example "lm"
	<Returns>
		the url for the installer
	"""

	user_key_dict = {}
	
	# generate keys for every owner and user
	for (percent, owner, users) in vessel_info:
		user_key_dict[owner] = __genkey__(owner)
		for u in users:
			user_key_dict[u] = __genkey__(u)

	return create_installer_with_keys(user_key_dict, vessel_info, dist_str)


# varies depends on how many users we have
# def create_installer_without_keys_with_equal_vessels(usernames):
#	create_installer_without_keys(vessels)


def create_installer_one_user(username, dist_str):
	"""
	<Purpose>
		Create the installe with only one user
	<Arguments>
		username:
			username of the user
		dist_str:
			string that contains any combination of letter w (Windows),
			l (Linux), or m (Mac). example "lm"
	<Returns>
		the url for the installer
	"""

	user_key_dict = {}
	user_key_dict[username] = __genkey__(username)
	
	# create the single-user vessel info
	vessel_info = [(8, username, [])]
	
	return create_installer_with_keys(user_key_dict, vessel_info, dist_str)


# default user key dictionary for testing purpose
user_key_dict = {"sean": "593515810385013851833", "ivan": "902039572093570927235", "justin": "9328446592099373728274", "peter": "834748293048249020810"}

# default vessel info for testing purpose
vessel_info = [(2, "sean", []), (3, "ivan", ["peter", "justin", "sean"]), (1, "peter", ["justin", "sean"])]

if __name__ == "__main__":
	print create_installer_with_keys(user_key_dict, vessel_info)