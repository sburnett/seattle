Protogeni XMLRPC Server Integration:

The Protogeni XMLRPC server integration is a way to integrate the 
SeattleGENI (Million-node GENI) project with the protogeni project.
It allows emulab users to to acquire and release SeattleGENI
resources. An emulab user can use their credential to access the 
XMLRPC server to acquire resources. The user can only use their 
emulab ssl certificate in order to be granted access.


Files that are required to run XMLRPC server:

  1. seattlegeni_xmlrpc_server.pl (included)
  2. generate_pubkey.py (included)
  3. seattlegeni_xmlrpc.logfile
  4. protogeni_user_file.txt
  5. protogeni_vessel_handle.txt
  6. genica.bundle
  7. genicrl.bundle
  8. __lockfile__
  9. seattlegeni_apache.conf



Setting up XMLRPC server:

  1. Create a folder where you want to have the XMLRPC server running
     from.

  2. Make sure that you have either all the seattle
     library files in the folder or have the seattle libraries in your
     PYTHONPATH. If you do not have the Seattle library files you can get it
     from our svn at https://seattle.cs.washington.edu/svn/seattle/trunk/
     Once you have checked out our repository, go into trunk and run the
     command:
    
     $> python preparetest.py /folder/to/copy/seattle_libraries_to
   
  3. Copy over the two files seattlegeni_xmlrpc_server.pl and
     generate_pubkey.py.

  4. From the list of files listed above, create the files 
     seattlegeni_xmlrpc.logfile, protogeni_user_file.txt, 
     protogeni_vessel_handle.txt, __lockfile__

  5. Download the two files genica.bundle and genicrl.bundle from 
     https://www.emulab.net/genica.bundle and 
     https://www.emulab.net/genicrl.bundle

  6. Set up the apache.conf file for apache. An example of what the 
     .conf file should look like is provided (seattlegeni_apache.conf)

  7. Make sure all the files that we copied over and created have the 
     right permissions. This is important as otherwise the server will 
     not right properly. To be safe you can use the command

     $> chmod 777 all_files_we_will_use

  8. Edit the file protogeni_user_file.txt and add all the seattlegeni
     users that have been specifically allocated for the protogeni integration.
     The format of each line is:

     seattlegeni_username:password_for_user:1:0:0

     The last 3 values are set by default to 1:0:0 but this will get changed
     to some other value after the XMLRPC server has run.

  9. Edit the seattlegeni_xmlrpc_server.pl file to make sure some of the global
     variables are set correctly. The variables that need to be changed are:
      * $generate_pubkey_path
      * $server_url
      * $protogeni_user_filename
      * $protogeni_vessel_handle_filename
      * $lockfile_path



Api calls provided in the XMLRPC server:
  1. CreateSliver()
  2. DeleteSlice()

You can visit our wiki page to learn more about the two calls and our XMLRPC 
server. The wiki page is located at: https://seattle.cs.washington.edu/wiki/ProtogeniIntegration



Testing the XMLRPC server:

We have provided the a test file that tests the two api calls. In order to run
it successfully, you will need a valid emulab certificate (emulab.pem) and must
have it in the same folder as the test file.
