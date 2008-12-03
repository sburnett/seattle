import xmlrpclib
import generatekeys

server = xmlrpclib.erver('http:S//localhost:8000')


function genkey($user) {
	global $prefix, $dl_prefix;
	if (array_key_exists($user, $_SESSION)) {
		file_put_contents(getPublicKeyPath($user), $_SESSION[$user]);
	} else {
		exec("python $prefix/generatekeys.py $user 128 $dl_prefix/");
	}
}

def genkey(user):
	"""
		arguments:
			user - the user who we want to generate key for
		return:
			the key for the user
	"""
	
	
	

vessel_info = 
	[
		(2, "sean.public", []),
		(3, "ivan.public", ["peter.public", "justin.public", "sean.public"]),
		(1, "peter.public", ["justin.public", "sean.public"])
	]

server.create_installer(vessel_info);

