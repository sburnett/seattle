import xmlrpclib
import generatekeys


def __genkey__(user):
	"""
		arguments:
			user - the user who we want to generate key for
		return:
			the key for the user
	"""
	

def create_installer_with_keys(user_key_dict, vessel_info):
	server = xmlrpclib.erver('http://localhost:8000')
	ret = server.create_installer(user_key_dict, vessel_info)
	return "Success!"
	# check errors
	# return something
	
def create_installer_without_keys(vessels):
	user_key_dict = {}
	for v in vessels:
		user_key_dict[v] = __genkey__(v)
	create_installer_with_keys(user_key_dict, vessels)
	
def create_installer_without_keys_with_equal_vessels(usernames):
	create_installer_without_keys(vessels)
	
#def create_installer_one_user(username):
	#...

user_keys_dict = {"sean": "5935158103850138518353", "ivan": "902039572093570927590235", "justin": "9328446592099373728274", "peter": "834748293048249020810"}

vessel_info = [(2, "sean", []), (3, "ivan", ["peter", "justin", "sean"]), (1, "peter", ["justin", "sean"])]

if __name__ == "__main__":
	print create_installer_with_keys(user_keys_dict, vessel_info)