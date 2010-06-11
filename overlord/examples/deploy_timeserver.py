import overlord

# Deploy the time server on 5 vessels
init_dict = overlord.init(GENI_USERNAME, 5, 'wan', 'time_server.py')
overlord.run(init_dict['geni_port'])
