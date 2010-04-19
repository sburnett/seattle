To run the controlled node communication servers, the following files in this directory must be copied into a test directory built by preparetest.py:

main executable files:
cncUpdateServer.repy
cncRegistrationServer.repy
cncQueryServer.repy

libraries:
cncFileParser.repy
cncSignData.repy
keyrangelib.repy

restriction file which should be used when starting the executable:
restrictions.cnc

topology description files:
cnc_server_list.txt - must list the update server addresses and public keys in format specified in cncFileParser.repy
cnc_backup_config.txt - must specify the server backup config in format specified in cncFileParser.repy 

Any registration servers or update servers that are not listed in the cnc_server_list.txt file, will not be trusted by the rest of the cnc system.