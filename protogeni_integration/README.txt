Protogeni XMLRPC Server Integration:

The Protogeni XMLRPC server integration is a way to integrate the 
SeattleGENI (Million-node GENI) project with the protogeni project.
It allows emulab users to to acquire and release SeattleGENI
resources. An emulab user can use their credential to access the 
XMLRPC server to acquire resources. The user can only use their 
emulab ssl certificate in order to be granted access.


Files that are required to run XMLRPC server:

  1. seattleclearinghouse_xmlrpc_server.pl (included)
  2. generate_pubkey.py (included)
  3. protogeni reference component files.
  4. seattleclearinghouse_xmlrpc.logfile
  5. protogeni_user_file.txt
  6. protogeni_vessel_handle.txt
  7. genica.bundle
  8. genicrl.bundle
  9. __lockfile__
  10. seattlegeni_apache.conf
  11. Seattle library files.


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

     (Note that running this command on a folder will delete any existing
     file already in that folder. It is best to do this on an empty folder,
     like in the one created in step 1.)   

  3. Download the Reference Component files from the Protogeni site and make
     sure that all the required libraries are downloaded and installed. 
     Instructions for all of this can be found at:
     https://www.protogeni.net/trac/protogeni/wiki/ReferenceCM

  4. Run the script prepare_seattlegeni_server.py with the command below
     where the target folder should be the folder created in step 1. This
     will copy/create/download the files that are required to run the xmlrpc
     server.
  
     $> python prepare_seattlegeni_server.py target_folder  

  5. Set up the .conf file for apache. An example of what the 
     .conf file should look like is provided (seattlegeni_apache.conf).
     A more detailed description on how to edit this file is located at the
     bottom of this file.

  6. Edit the file protogeni_user_file.txt and add all the seattlegeni
     users that have been specifically allocated for the protogeni integration.
     You can acquire seattlegeni usernames by registering an username through 
     the SeattleGENI website at: https://seattlegeni.cs.washington.edu
     The format of each line in protogeni_user_file.txt is:

     seattlegeni_username:password_for_user:1:0:0

     The last 3 values are set by default to 1:0:0 but this will get changed
     to some other value after the XMLRPC server has run.

  7. Edit the seattleclearinghouse_xmlrpc_server.pl file to make sure some of the global
     variables are set correctly if not done so already. The variables that 
     need to be changed if necessary are:
      * $generate_pubkey_path
      * $server_url
      * $protogeni_user_filename
      * $protogeni_vessel_handle_filename
      * $lockfile_path

   8. Edit the generate_pubkey.py file to make sure that the correct path has
      been set for the Seattle library files. The directory path for the Seattle 
      library files is the same path as the directory where Seattle files 
      were extracted to in Step 2.


Api calls provided in the XMLRPC server:
  1. CreateSliver()
  2. DeleteSlice()

You can visit our wiki page to learn more about the two calls and our XMLRPC 
server. The wiki page is located at: https://seattle.cs.washington.edu/wiki/ProtogeniIntegration



Configuring the seattlegeni_apache.conf file:

This is a just a very simple description of how to configure the .conf file. More complicated
configuration could be done if necessary. In order to configure the .conf file properly, the
following variables must be modified:

  * The path of the log files must be set correctly. So any errors and access logs are 
    recorded properly.
  * You must have a valid SSL Certificate and set the path to the Certificate file (Line 42)
  * The path for SSLCACertificateFile and SSLCARevocationFile must be set in line 45-46. 
    When the prepare_seattlegeni_server.py file was ran in Step 4, the two files genica.bundle
    and genicrl.bundle should have been downloaded to the target_folder. Use the file path of 
    these two files as the path for SSLCACertificateFile and SSLCARevocationFile. If the two
    files were not downloaded, then they could be downloaded here:
  
      https://www.emulab.net/genica.bundle
      https://www.emulab.net/genicrl.bundle
   
    These files are used to grant access to emulab users.
  * The path to the seattleclearinghouse_xmlrpc_server.pl should be set for the variable ScriptAlias
    in line 49.
  * The directory where the  XMLRPC server resides should be set at line 51 as the directory path.
  * The location of the Seattle library files that were extracted in Step 2, should be added to 
    the pythonpath in line 61 of the .conf file.

More tutorials on how to configure apache files can be found at the apache website at
http://httpd.apache.org/ under the documentation section.



Testing the XMLRPC server:

We have provided the a test file that tests the two api calls. In order to run
it successfully, you will need a valid emulab certificate (emulab.pem) and must
have it in the same folder as the test file. The test file must also be modified
slightly to include the right certificate and the right filepath for certificate.


If you have any questions please contact Monzur Muhammad at monzum@cs.washington.edu
or Justin Cappos at justinc@cs.washington.edu
