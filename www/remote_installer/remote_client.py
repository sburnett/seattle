import xmlrpclib

server = xmlrpclib.erver('http:S//localhost:8000')


vessel_info = 
	[
		(2, "sean.public", []),
		(3, "ivan.public", ["peter.public", "justin.public", "sean.public"]),
		(1, "peter.public", ["justin.public", "sean.public"])
	]

server.create_installer(vessel_info);


# print server.chop_in_half('I am a confidant guy')
# print server.repeat('Repetition is the key to learning!\n', 5)
# print server._string('<= underscore')
# print server.python_string.join(['I', 'like it!'], " don't ")
# print server._privateFunction() # Will throw an exception
