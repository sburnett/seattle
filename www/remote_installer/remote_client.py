import xmlrpclib
import generatekeys



function genkey($user) {
	global $prefix, $dl_prefix;
	if (array_key_exists($user, $_SESSION)) {
		file_put_contents(getPublicKeyPath($user), $_SESSION[$user]);
	} else {
		exec("python $prefix/generatekeys.py $user 128 $dl_prefix/");
	}
}

def __genkey__(user):
	"""
		arguments:
			user - the user who we want to generate key for
		return:
			the key for the user
	"""

def create_installer_with_keys(user_key_dict, vessels):
	server = xmlrpclib.erver('http://localhost:8000')
	ret = server.create_installer(user_key_dict, vessels)
	# check errors
	# return something
	
def create_installer_without_keys(vessels):
	user_key_dict = {}
	for v in vessels:
		user_key_dict[v] = __genkey__(v)
	create_installer_with_keys(user_key_dict, vessels)
	
def create_installer_without_keys_with_equal_vessels(usernames):
	create_installer_without_keys(vessels)
	
def create_installer_one_user(username):
	# ...

vessel_info = [ {"sean": "5935158103850138518353", "ivan": "90572039572093570927590235"},\
				(2, "sean", []),\
				(3, "ivan", ["peter", "justin", "sean"]),\
				(1, "peter", ["justin", "sean"])]
