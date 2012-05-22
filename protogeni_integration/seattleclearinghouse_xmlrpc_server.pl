#!/usr/bin/perl -w

use Frontier::Client;
use Frontier::Responder;
use Frontier::RPC2;
use POSIX;
use RPC::XML::Client;
use Time::HiRes qw ( sleep );
use warnings;
use strict;

use lib '/path/to/protogeni/reference-cm-2.0/xmlrpc';
use lib '/path/to/protogeni/reference-cm-2.0/lib';
use GeniResponse;
use GeniHRN;
use GeniCredential;

use XML::Simple;
use XML::LibXML;


# Yack. apache does not close fds before the exec, and if this dies
# we are left with a giant mess.
BEGIN {
  no warnings;
  for (my $i = 3; $i < 2048; $i++) {
    POSIX:close($i);
  }
}



my $debug = 0;


my $directory_prefix = "/path/to/xmlrpc/server/location/";
my $generate_pubkey_path = $directory_prefix . "generate_pubkey.py";

# Url for the seattlegeni xmlrpc server.
my $server_url = 'https://seattlegeni.cs.washington.edu/xmlrpc/';

# These two dictionary keeps track of which seattlegeni users are
# available, and what their password is.
my %protogeni_user_available = ();
my %protogeni_user_pass = ();
my %protogeni_user_resource_dict = ();
my $time_to_expire_resource = 4 * 3600; # Usually resource expires after 4 hour.

################################################################################################
# The format of the 3 dictionaries above.
#
# %protogeni_user_available = {username : {'available' : 1_or_0,
#                                          'time_acquired' : "A timestamp of when resource was allocated for user.",
#                                          'api_key' : "Current api key associated with the username."
#                                         }
#
# %protogeni_user_pass = {username : password}
#
# %protogeni_user_resource_dict = {slice_urn : {'seattle_username' : "The seattle username associated with the slice_urn,
#                                               'vessel_handles' : @list_of_vessel_handles
#                                              }
#################################################################################################


my $protogeni_user_filename = $directory_prefix . "protogeni_user_file.txt";
my $protogeni_vessel_handle_filename = $directory_prefix . "protogeni_vessel_handle.txt";
my $lockfile_path = $directory_prefix . "__lockfile__";

################################################################################################
# The format of the two important files.
#
# <protogeni_user_file.txt>
#   seattle_username:password:availability:timestamp_of_last_resource_acquisition:last_known_api_key
#
#   Every item is has a ':' delimeter in between.
#
# <protogeni_vessel_handle.txt>
#   slice_urn=seattle_username=list_of_handles_that_are_comma_seperated
#
#   The three items have the '=' delimeter in between, and the list of vessel handles
#   have a ',' delimeter in between them.
#
################################################################################################


# The different type of file lock codes: shared lock, exclusive lock,
# unlock, and LOCK_NB is for non-blocking lock.
my $LOCK_SH = 1;
my $LOCK_EX = 2;
my $LOCK_UN = 8;
my $LOCK_NB = 4;


# Logging type code.
my $NORMAL_LOG = 0;
my $ERROR_LOG = 1;

my $log_filepath = $directory_prefix . "seattleclearinghouse_xmlrpc.logfile";



sub main {

  # If the request is not a POST type, then display a html page.
  if ($ENV{'REQUEST_METHOD'} ne 'POST') {
    display_info_page();
    exit(0);
  }

  if( !defined( $ENV{'SSL_CLIENT_CERT'} ) ) {
      my $decoder = Frontier::RPC2->new();
      print "Content-Type: text/xml \n\n";
      print $decoder->encode_fault(-1, "No client certificate");
      exit(0);
  }

  print "Content-Type: text/txt\n\n";

  # Setup and open up the logfile.
  setup_log_file();

  # Parse the SSL certificate and extract the GeniUSER from the certificate,
  # this is used later to do some security checks.
  my $client_cert = GeniCertificate->LoadFromString( $ENV{'SSL_CLIENT_CERT'}, 1 );
  printlog("User connecting to xmlrpc server: " . $client_cert->urn());
  $ENV{'GENIUSER'} = $ENV{'GENIURN'} = $client_cert->urn();

  # Open up the user file that contains the SeattleGENI users and
  # their passwords, and fill up the necessary variables.
  retrieve_user_file();

 
  # Get a CGI version of the server.
  my $request = Frontier::Responder::get_cgi_request();
  if (!defined($request)) {
    print "Content-Type: text/txt\n\n";
    exit(0);
  }

  #
  # Create and set our RPC context for any calls we end up making.
  # We are only going to support the two calls CreateSliver and
  # DeleteSlice.
  #
  my $response_methods = Frontier::Responder->new( "methods" => {
    "CreateSliver"      => \&CreateSliver,
    "DeleteSlice"       => \&DeleteSlice,
  } );


  # Note that response_methods->{'_decode'} is the same as Frontier::RPC2->new()
  # Create and server the xmlrpc server for SeattleGENI Component Manager.
  my $response = $response_methods->{'_decode'}->serve($request, $response_methods->{'methods'});


  if ($debug) {
      print TEST_FILE "\nin debugger\n";
      my $decoder = Frontier::RPC2->new();
      my $object  = $decoder->decode($response);
      my $value   = $object->{'value'};
  }

  # Now that we have finished the task, we want to write all our dictionaries
  # to file so we can use the info later.
  write_user_file();  
   
  print $response;
  exit(0)
}






sub display_info_page() {
  # Display an html info page about the seattle xmlrpc integration server
  print "Content-type: text/html\n\n";
  print "<html><head>\n";
  print "<title>SeattleGENI XMLRPC Integration Server</title>";
  print "</head>\n<body>";
  print "<b>This is the XMLRPC server for integration with the protogeni project.</b><br>";
  print "</body>\n</html>";
}




sub retrieve_user_file() {
  #
  # <Purpose>
  #   Open up the file containing the protogeni usernames and their password
  #   and fill up the two hashtables that keep track of the usernames and 
  #   their password. As well open up the file containing the dictionary
  #   of the users who have already acquired resources and fill in the 
  #   dictionary assigning the vesselhandles to the protogeni users.
  #  
  # <Arguments>
  #   None
  #
  # <Side_Effects>
  #   Files are opened and read.
  #
  # <Exception>
  #   If the file can't be opened, we kill the program.
  #
  # <Return>
  #   None
  #

  # Open the file and on exception close the file and exit.
  eval{
    open (USER_FILE, "<", $protogeni_user_filename) or 
      die "Can't open the file $protogeni_user_filename. Make sure the file exists";
    open (VESSELHANDLE_FILE, "<", $protogeni_vessel_handle_filename) or
      die "Can't open the file $protogeni_vessel_handle_filename. Make sure the file exists";
    open (LOCKFILE, ">>", $lockfile_path) or
      die "Could not grab lockfile"; 
  };
  if ($@) {
    printlog($@, $ERROR_LOG);
    printlog("Exiting program\n");  
    exit(1);
  }

  # Maximum time to wait to acquire lock on user file.
  my $total_sleep = 0;

  while(!(flock(LOCKFILE, $LOCK_EX))){
    # Sleep for 0.1 sec, however dont' wait around for ever,
    # If we have slept more then 5 sec then just exit.
    sleep(0.1);
    $total_sleep += 0.1;
    
    if ($total_sleep > 3){
      printlog("Could not acquire lock for $lockfile_path.\nExiting program\n", $ERROR_LOG);
      exit(1);
    } 
  }


  my @vesselhandle_line;

  # Read the file that keeps track of the protogeni users and what vesselhandles are 
  # associated with them, and load them up.
  while(my $line = <VESSELHANDLE_FILE>){
      chomp($line);
      if($line) {
        @vesselhandle_line = split('=', $line);

        my $slice_urn = $vesselhandle_line[0];
        my $seattle_username = $vesselhandle_line[1];
        my $list_handle_string = $vesselhandle_line[2];


	my @list_handles = split(',', $list_handle_string);
	$protogeni_user_resource_dict{$slice_urn} = {'vessel_handles', \@list_handles,
                                                     'seattle_username', $seattle_username};
      }
  }

  
  my @user_line;

  # Read each line of the file and fill in the username and password for
  # the SeattleGENI accounts.
  printlog("Loading SeattleGENI user file.");
  while(my $line = <USER_FILE>){
    chomp($line);
    @user_line = split(':', $line);

    my $username = $user_line[0];
    my $password = $user_line[1];
    my $availability = $user_line[2];
    my $resource_timestamp = $user_line[3];
    my $api_key = $user_line[4];

    $protogeni_user_pass{$username} = $password;
    $protogeni_user_available{$username} = {'available', $availability, 'time_acquired', $resource_timestamp,
                                            'api_key', $api_key};

    # Check if the timestamp was $time_to_expire_resource seconds ago. If so then the username is available
    # again and we want to release the vessel handles associated with it.
    my $time_diff = time - $protogeni_user_available{$username}->{'time_acquired'};
    my $current_time = time;
    my $resource_time = $protogeni_user_available{$username}->{'time_acquired'};

    printlog("the time difference is $time_diff, xpire time is $time_to_expire_resource");
    printlog("Currentime: $current_time, resource_time: $resource_time");

    if ( (time - $protogeni_user_available{$username}->{'time_acquired'}) > $time_to_expire_resource) {
	$protogeni_user_available{$username}->{'available'} = 1;
        printlog("Time has expired for user: $username.");
    }

    # If the user is now available, due to expired time or perhaps
    # because the resource was released, then we want to delete it
    # from the dictionary.
    if ($protogeni_user_available{$username}->{'available'}){
      foreach my $slice_urn_key (keys %protogeni_user_resource_dict) {
	if ($protogeni_user_resource_dict{$slice_urn_key}->{'seattle_username'} eq $username) {
          delete($protogeni_user_resource_dict{$slice_urn_key});
          printlog("Deleting slice_urn: $slice_urn_key from resource dict.");
	}
      }
    }

    printlog("Setting values for user $username: availabilit=$protogeni_user_available{$username}->{'available'}, resource_timestamp=$resource_timestamp, api_key=$api_key");
  }

  close (USER_FILE);
  close (VESSELHANDLE_FILE);
}



sub write_user_file {
  #
  # <Purpose>
  #   We have a dictionary that holds the user, along with its password
  #   and weather the user is available, and the timestamp when resource
  #   was allocated to that user.
  #
  # <Arguments>
  #   None.
  #
  # <Side Effects>
  #   Files are opened and written to.
  #
  # <Exception>
  #   None.
  #
  # <Return>
  #   None.
  #

  # Open up the user file and the vessel handle file in order to write info
  # in them.
  eval{
    open (USER_FILE, ">", $protogeni_user_filename) or
      die "Can't open the file $protogeni_user_filename. Make sure the file exists";
    open (VESSELHANDLE_FILE, ">", $protogeni_vessel_handle_filename) or
      die "Can't open the file $protogeni_vessel_handle_filename. Make sure the file exists";
    };
  if ($@) {
    printlog($@, $ERROR_LOG);
    printlog("Exiting program\n");
    exit(1);
  }

  
  # Go through all the user names and write their info to file.
  foreach my $username (keys (%protogeni_user_available)) {
    my $printline = "$username:$protogeni_user_pass{$username}:$protogeni_user_available{$username}->{'available'}:".
        "$protogeni_user_available{$username}->{'time_acquired'}:$protogeni_user_available{$username}->{'api_key'}\n";

    print USER_FILE "$username:$protogeni_user_pass{$username}:$protogeni_user_available{$username}->{'available'}:".
	"$protogeni_user_available{$username}->{'time_acquired'}:$protogeni_user_available{$username}->{'api_key'}\n";
    printlog("Writing to USER_FILE: $printline");

  }

  printlog("Wrote users and their availability to $protogeni_user_filename");

  # Write all the info about vesselhandles to the vesselhandle file.
  foreach my $username (keys (%protogeni_user_resource_dict)) {
    my $vesselhandle_list = $protogeni_user_resource_dict{$username}->{'vessel_handles'};
    my $seattle_username = $protogeni_user_resource_dict{$username}->{'seattle_username'};
    my $vessel_line = "$username=$seattle_username=".join(",", @$vesselhandle_list)."\n";
   
    printlog("Writing to VESSELHANDLE_FILE: $vessel_line");
    print VESSELHANDLE_FILE "$username=$seattle_username=".join(",", @$vesselhandle_list)."\n";
  }

  printlog("Wrote users and the vessel handles associated with them to $protogeni_vessel_handle_filename");

  close (USER_FILE);
  close (VESSELHANDLE_FILE);
}




sub CreateSliver($) {

  #
  # <Purpose>
  #   From SeattleGENI's point of view, we acquire vessels for a particular
  #   user with a particular API key.
  #
  # <Arguments>
  #   * slice_urn - in seattle terms this is the username.
  #   * rspecstr - this converts directly to the rspec for SeattleGENI.
  #   * credentials - this would be some seattlegeni credential that will be hopefully,
  #     converted to an API key for Seattle users.
  #   * keys - this will probably be optional and most likely will not be used.
  #   * impotent - this was not defined in the api, so we might get rid of this later.
  #
  # <Side Effects>
  #   None
  #
  # <Exceptions>
  #   All errors and exceptions are sent back as Geni Respones.
  #
  # <Return>
  #   {'sliver': string_form, 'mainfest': string_form}
  # 

  my ($argref) = @_;
  my $slice_urn    = $argref->{'slice_urn'};
  my $rspecstr     = $argref->{'rspec'};
  my $credentials  = $argref->{'credentials'};
  my $keys         = $argref->{'keys'} || 0;
  my $impotent     = $argref->{'impotent'} || 0;
  
  printlog("CreateSliver is called with slice_urn: $slice_urn, rspec: $rspecstr");
  
  # Ensure that credentials, slice_urn, and rspecstr are defined
  if (! (defined($credentials) && defined($slice_urn) && defined($rspecstr))) {
    printlog("Could not complete request due to missing argument of slice_urn, rspec or credentials");
    return GeniResponse->MalformedArgsResponse("Missing arguments");
  }

  # If the user has already acquired resources, then deny it.
  if (exists( $protogeni_user_resource_dict{$slice_urn})){
    printlog("Could not complete request. Resource already allocated for $slice_urn");
    return GeniResponse->Create(GENIRESPONSE_REFUSED, undef, "Resource already allocated for requested for slice_urn: $slice_urn");
  }


  # Make sure that rspecstr is in right format.
  if (! ($rspecstr =~ /^[\040-\176\012\015\011]+$/)) {
    printlog("Could not complete request. Malformed respec string.");
    return GeniResponse->MalformedArgsResponse("Bad characters in rspec");
  }

  # make sure that the slice_urn is valid. This is the user name.
  if (! GeniHRN::IsValid($slice_urn)) {
    printlog("Could not complete request. slice_urn is not valid.");
    return GeniResponse->MalformedArgsResponse("Bad characters in URN");
  }

  # Check the credential that they provided.
  my $checked_credential = CheckCredentials($credentials);

  # Check the credential that 
  if (GeniResponse::IsResponse($checked_credential)){
    printlog("Could not complete request. Credential does not check out");
    return $checked_credential;
  }

  # Make sure that the slice urn matches the owner_urn of the credential
  # that was provided.
  if ($checked_credential->{'target_urn'} ne $slice_urn) {
    printlog("Invalid slice_urn provided...");
    printlog("Slice_urn provided: $slice_urn. Target slice is: $checked_credential->{'target_urn'}.");
    return GeniResponse->Create(GENIRESPONSE_FORBIDDEN, undef,
                                "This is not your credential. Invalid slice_urn provided.");
  }

  printlog("Credential checks out for slice: $slice_urn");


  # Variables used to store the seattle credential and public key string.
  my $seattle_credential;
  my $pubkey_string;

  if (get_available_user()) {        
    # Note that $seattle_credential is in the form of seattle authentication.
    ($seattle_credential, $pubkey_string) = get_seattlegeni_credentials();
    printlog("Retrieved username: " . $seattle_credential->{'username'} . " to allocate resource to.");
  } else {
      printlog("Could not complete request. There aren't any more SeattleGENI user left to allocate resources to.");
      return GeniResponse->Create(GENIRESPONSE_UNAVAILABLE, undef, "Requesting more resources then available");
  }


  # Check if there was any error while retrieving the SeattleGENI credentials.
  if (GeniResponse::IsResponse($seattle_credential)){
      printlog("Could not complete request. Was unable to retrieve SeattleGENI credentials.");
      return $seattle_credential;
  }



  # This is the rspec that is used to call the seattlegeni xmlrpc server.
  # Also convert the rspec from string to int form.
  my %seattlegeni_rspec = ('rspec_type', 'random', 'number_of_nodes', 1*$rspecstr);

  # Acquire the resources using the seattlegeni xmlrpc server.
  my $acquire_resource_result = acquire_resources($seattle_credential, \%seattlegeni_rspec);



  # Check if we were able to acquire resources, if not we return the GeniResponse.
  if (GeniResponse::IsResponse($acquire_resource_result)){
      printlog("Could not complete request. Was unable to acquire resources from SeattleGENI");
      return $acquire_resource_result;
  }


  printlog("Successfully acquired resources for the user: " . $seattle_credential->{'username'});

  # Convert the return result from the SeattleGENI xmlrpc server to something that
  # protogeni can understand, a GENIRESPONSE.
  my $vessel_handle_list = parse_acquired_resource_result($acquire_resource_result, $slice_urn, $seattle_credential->{'username'});

  ################ RETURN SOMETHING!!! ####################

  # This is the info that is needed to access the resources
  my $resource_info = {'api_key', $seattle_credential->{'api_key'},
                  'publickey_string', $pubkey_string,
		  'vesselhandle_list', {'vesselhandle', $vessel_handle_list} };

  # Create the manifest in XML form.
  my $manifest = {};
  $manifest->{'xmlns'} = "https://blackbox.cs.washington.edu/xmlrpc/";
  $manifest->{'xmlns:xsi'} = "http://www.w3.org/2001/XMLSchema-instance";
  $manifest->{'xsi:schemaLocation'} = "https://blackbox.cs.washington.edu/~geni/seattle_manifest.xsd";
  $manifest->{'generated'} = "today";
  $manifest->{'generated_by'} = "SeattleGENI";
  $manifest->{'type'} = "response";
  $manifest->{'node'} = $resource_info;  

  my $return_result = {};
  $return_result->{'sliver'} = "urn:publicid:IDN+SeattleGENI+user+" . $seattle_credential->{'username'};
  $return_result->{'manifest'} = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n" . XMLout($manifest, RootName => 'rspec');

  return GeniResponse->Create(GENIRESPONSE_SUCCESS, $return_result);                                  
}





sub DeleteSlice ($) {

  #
  # <Purpose>
  #   From SeattleGENI's point of view, we acquire vessels for a particular
  #   user with a particular API key.
  #
  # <Arguments>
  #   * slice_urn - in seattle terms this is the username.
  #   * credentials - this would be some seattlegeni credential that will be hopefully,
  #     converted to an API key for Seattle users.
  #   * impotent - this was not defined in the api, so we might get rid of this later.
  #
  # <Side Effects>
  #   None
  #
  # <Exceptions>
  #   All errors and exceptions are sent back as Geni Respones.
  #
  # <Return>
  #   A GeniResponse thats either a success or some kind of error.
  #

  my ($argref) = @_;
  my $slice_urn    = $argref->{'slice_urn'};
  my $credentials  = $argref->{'credentials'};
  my $impotent     = $argref->{'impotent'} || 0;


  printlog("DeleteSlce is called with slice_urn: $slice_urn");

  # Ensure that credentials, slice_urn, and rspecstr are defined
  if (! (defined($credentials) && defined($slice_urn))) {
    printlog("Could not complete request due to missing argument of slice_urn, rspec or credentials");
    return GeniResponse->MalformedArgsResponse("Missing arguments");
  }

  # make sure that the slice_urn is valid. This is the user name.
  if (! GeniHRN::IsValid($slice_urn)) {
      printlog("Could not complete request. slice_urn is not valid.");
      return GeniResponse->MalformedArgsResponse("Bad characters in URN");
  }

  # Check the credential that they provided.
  my $checked_credential = CheckCredentials($credentials);

  # Check the credential that
  if (GeniResponse::IsResponse($checked_credential)){
    printlog("Could not complete request. Credential does not check out");
    return $checked_credential;
  }

  # Make sure that the slice urn matches the owner_urn of the credential
  # that was provided.
  if ($checked_credential->{'target_urn'} ne $slice_urn) {
      printlog("Invalid slice_urn provided...");
      printlog("Slice_urn provided: $slice_urn. Target slice is: $checked_credential->{'target_urn'}.");
    return GeniResponse->Create(GENIRESPONSE_FORBIDDEN, undef,
                                "This is not your credential. Invalid slice_urn provided.");
  }


  printlog("Credential checks out for slice: $slice_urn");

  if (! exists($protogeni_user_resource_dict{$slice_urn})) {
    printlog("Could not complete request. The slice $slice_urn not found.");
    return GeniResponse->Create(GENIRESPONSE_SEARCHFAILED, undef, "The slice $slice_urn does not exist!");
  }

  printlog("Found the slice_urn: $slice_urn to be deleted.");

  # Create and retrieve a seattlegeni authentication from the slice_urn
  # that was provided. Also retrieve the list of vessel handles that are
  # associated with the slice_urn.
  my $seattlegeni_auth = get_seattlegeni_auth($slice_urn);
  my $vessel_handle_list = $protogeni_user_resource_dict{$slice_urn}->{'vessel_handles'};

  # Delete/release the resources associated with the slice_urn
  my $delete_resources_result = release_resources($seattlegeni_auth, $vessel_handle_list);  

  if (GeniResponse::IsResponse($delete_resources_result)){
      printlog("Could not complete request. Was unable to release the resources associated with the slice $slice_urn");
      return $delete_resources_result;
  }  

  printlog("Successfully deleted the slice for the slice_urn: $slice_urn");

  # Remove the list of vessel handles that are associated with the slice_urn
  # from the dictionary holding the slice_urn->vesselhandle info.
  # Also release the SeattleGENI username associated with the slice_urn,
  # so the username can be used again.
  delete($protogeni_user_resource_dict{$slice_urn});
  $protogeni_user_available{$seattlegeni_auth->{'username'}}->{'available'} = 1;
  
  # If we got to this point then everything was a success! So we return a 
  # Success GeniResponse.
  return GeniResponse->Create(GENIRESPONSE_SUCCESS);

}





sub parse_acquired_resource_result {
  # 
  # <Purpose>
  #   After we have acquired the result, we want to take apart the return
  #   result from the SeattleGENI xmlrpc server and turn it into a result
  #   that we can return from this xmlrpc server to the protogeni folks.
  #
  # <Arguments>
  #   acquire_resource_result - this is the result that is returned from 
  #     the SeattleGENI xmlrpc server.
  #
  #   slice_urn - this is the slice name or the urn that was provided by 
  #     geni user.
  #
  # <Exception>
  #   None.
  # 
  # <Side Effects>
  #   None.
  #
  # <Return>
  #   A properly formatted GENI response.
  #

  my $acquired_resource_result = shift (@_);
  my $slice_urn = shift (@_);
  my $seattle_username = shift (@_);

  # The result returns a dictionary with information about each of the vessels
  # or resources that were allocated. We want to go deep into each of these
  # vessel information and retrieve the vessel handles, so we can store them.
  # These vessel handles are needed later on to release the resources.
  my @result_array =  @$acquired_resource_result;
  my @acquired_vessel_handles = ();

  foreach my $vessel_info_dict (@result_array){
    my %vessel_info = %$vessel_info_dict;
    printlog("Allocated vessel: " . $vessel_info{"handle"} . " for user: $slice_urn");
    push(@acquired_vessel_handles, $vessel_info{"handle"});
  }

  # Now that we have retrieved all the vessel handles, we are going to
  # store it in a dictionary with the slice_urn as the key.
  $protogeni_user_resource_dict{$slice_urn} = {'vessel_handles', \@acquired_vessel_handles,
                                               'seattle_username', $seattle_username};

  return \@acquired_vessel_handles;

}





sub get_seattlegeni_auth {
  #
  # Given a slice_urn, return a seattlegeni authentication.
  #

  my $slice_urn = shift (@_);

  my $seattle_username = $protogeni_user_resource_dict{$slice_urn}->{'seattle_username'};
  my $api_key = $protogeni_user_available{$seattle_username}->{'api_key'};
  my %seattlegeni_auth;

  printlog("We are creating seattle authentication with username: $seattle_username, and api_key: $api_key");

  $seattlegeni_auth{'username'} = $seattle_username;
  $seattlegeni_auth{'api_key'} = $api_key;

  return \%seattlegeni_auth;
}




sub get_seattlegeni_credentials() {

  #
  # <Purpose>
  #   This is where we retrieve a seattlegeni user and their credential that
  #   we will use later on to acquire resources. There are several dedicated
  #   username for the protogeni integration. Each time CreateSliver is called,
  #   we will take one of these user names that are available and return its
  #   credentials. In this case the credentials are the username, the api key,
  #   and the publick key string. Every time we find an available user name,
  #   we have to regenerate its api key, and assign it a new random public key
  #   string. This is because a previous user may still hold on to the old api
  #   key and public key string, and we don't want them to have access to the
  #   new resources that we will allocate for the current user. This way we 
  #   ensure that only the current user has access to the newly allocated 
  #   resources.
  #
  #  <Arguments>
  #    None.
  # 
  #  <Side Effects>
  #    We call the seattlegeni xmlrpc server twice.
  #
  #  <Exceptions>
  #    If all the usernames are active and are being used right now, we are 
  #    going to respond with an 'unavailable resources' response.
  #
  #  <Return>
  #    We are going to return the seattlegeni authentication which is the
  #    username and the new api key. We will also return  the new 
  #    public key string.
  #    seattlegeni_auth{'username': "some_username",
  #                     'api_key': "the_new_api_key"}
  #    publickey_string - the new public key string.
  #
  
  my %seattlegeni_auth;
  my $seattle_username = get_available_user();

  # If we found an available user that was not being used, we use
  # it as part of our seattlegeni credential.
  if ($seattle_username){ 
    $seattlegeni_auth{'username'} = $seattle_username;
  } 


  # This is the password authentication. It is used to regenerate the api key for a user
  # and to set the public key string for a particular user.
  my %pwauth = ('username', $seattle_username, 'password', $protogeni_user_pass{$seattle_username});

  # Client used to make api calls to SeattleGENI.
  my $server = Frontier::Client->new('url' => $server_url);




  # The variable that will hold the result after the xmlrpc call to seattlegeni.
  my $new_api_key;
  # Make the call on the server side to regenerate the api key for the particular user.
  eval {
    $new_api_key = $server->call('regenerate_api_key', \%pwauth);
  };
  if($@) {
    # If there was a problem changing the api key, we return an error message.
    printlog("Unable to regenerate api_key for user: $seattle_username");
    return GeniResponse->Create(GENIRESPONSE_ERROR, undef, "Internal error with SeattleGENI");
  }    

  printlog("Generated new api_key for user $seattle_username: $new_api_key");
  
  # Assign the new api key in the seattlegeni authentication.
  $seattlegeni_auth{'api_key'} = $new_api_key;


  # Generate a new public key string that we will use to set a 
  # new public key for a certain seattlegeni user.
  my $new_pubkey_string = generate_pubkey();

  # We are going to set a new public key string for the current user
  # because we don't know if someone still has the old credential 
  # for the current user. Which is why we regenerated the api key, 
  # and now we are going to set a new random publick key for the user.
  eval {
    $server->call('set_public_key', \%pwauth, $new_pubkey_string);
  };
  if($@) {
    # If there was a problem changing the api key, we return an error message.
    printlog("Unable to change the public_key for user: $seattle_username");
    return GeniResponse->Create(GENIRESPONSE_ERROR, undef, "Internal error with SeattleGENI");
  }    

  printlog("Successfully set a new public key for user: $seattle_username");

  # Return the seattlegeni credentials, api_key and public key string.
  return (\%seattlegeni_auth, $new_pubkey_string);
}





sub generate_pubkey() {
  #
  # Our Seattle library was written in python, so we needed to create
  # a python script that simply generates a random public key string
  # and prints it to the console. We just call the script and capture
  # its output and return the result.
  #
 
  my @key_result = `/usr/bin/python $generate_pubkey_path`;
  return $key_result[0];
}




sub get_available_user() {
  #
  # Check if any user are available. If they are return user name,
  # else return 0.
  #
  foreach my $username (keys %protogeni_user_available){
    #
    # Go through all the users that are available for the protogeni
    # group and check which ones are still available.
    # If we find an available user we return it.
      if ($protogeni_user_available{$username}->{'available'}){
	return $username;
      }
  }

  return 0;
}




sub CheckCredentials($) {

  #
  # <Purpose>
  #   Initial credential check.
  #
  # <Argument>
  #   List of credentials
  # 
  # <Return>
  #   The extracted items from credential if the credential is legit, 
  #   otherwise return a GeniResponse.
  #

  my @credentials = @{ $_[0] };

  if (scalar(@credentials) != 1) {
    return
      GeniResponse->MalformedArgsResponse("Wrong number of credentials");
  }

  my $parser = XML::LibXML->new;
  my $parsed_xml_doc;
  eval {
    $parsed_xml_doc = $parser->parse_string($credentials[0]);
  };
  if ($@) {
    print STDERR "Failed to parse credential string: $@\n";
    return undef;
  }

  # Ensure that some of the key elements exist in the credential.
  if (!defined($parsed_xml_doc->getElementsByTagName("privileges"))){
    printlog("A credential object could not be created");
    return GeniResponse->Create(GENIRESPONSE_ERROR, undef, "Could not create credential object");
  }
  if (!defined($parsed_xml_doc->getElementsByTagName("owner_urn"))){
    printlog("A credential object could not be created");    
    return GeniResponse->Create(GENIRESPONSE_ERROR, undef, "Could not create credential object");
  }
  if (!defined($parsed_xml_doc->getElementsByTagName("target_urn"))){
    printlog("A credential object could not be created");
    return GeniResponse->Create(GENIRESPONSE_ERROR, undef, "Could not create credential object");
  }

  # Extract the certificate from the credential.
  my $certificate_provided = $parsed_xml_doc->getElementsByTagName("signatures")->to_literal();
  my $certificate_actual = $ENV{'SSL_CLIENT_CERT'};
  chomp($certificate_provided);
  chomp($certificate_actual);  

  # Make sure that the certificate provided checks out with what the certificate
  # is supposed to be.
  if ($certificate_provided ne $certificate_actual) {
    printlog("Incorrect credential provided by user. The credential may not be from user.");
    printlog("Credential provided: " . $certificate_provided);
    printlog("Credential should be: " . $certificate_actual);
    return GeniResponse->Create(GENIRESPONSE_ERROR, undef, "Incorrect credential provided");
  }

  my $credential = {};

  
  $credential->{'owner_urn'} = $parsed_xml_doc->getElementsByTagName("owner_urn")->to_literal();
  $credential->{'target_urn'} = $parsed_xml_doc->getElementsByTagName("target_urn")->to_literal();
  
  #
  # Make sure the credential was issued to the caller.
  #

  printlog("Parsing credential. credential owner_urn is: " . $credential->{'owner_urn'} . 
    ", target_urn is: " . $credential->{'target_urn'} );

  # Make sure that the right user is trying to access resources.
  if ($credential->{'owner_urn'} ne $ENV{'GENIURN'}) {
    return GeniResponse->Create(GENIRESPONSE_FORBIDDEN, undef,
				"This is not your credential");
  }

  return $credential;
}





sub acquire_resources {
  
  # Extract the two arguments. Both the arguments are dictionaries and the format
  # is as follows:
  # %auth: {'username':'YOUR_USER_NAME', 'api_key':'YOUR_API_KEY'}
  # %rspec: {'rspec_type':'LAN_WAN_OR_NAT_TYPE', 'number_of_nodes': N}

  my($auth_ref, $rspec_ref) = @_;

  my $server = Frontier::Client->new('url' => $server_url);

  # The variable that will hold the result after the xmlrpc call to seattlegeni.
  my $server_call_result;

  # Make the call on the server side to acquire resources for the user with the 
  # specifications provided.

  eval { 
    $server_call_result = $server->call('acquire_resources', $auth_ref, $rspec_ref);
  };
  if ($@) {
    # If there was any error and any reason why we couldn't acquire resource, then
    # we return a GeniResponse with a GENIRESPONSE_ERROR code.
    printlog("Was unable to acquire resource. Returned with error: $@");
    return GeniResponse->Create(GENIRESPONSE_ERROR, undef, "Unable to allocate resources.");
  }

  # Once we have acquired the resource for the current user, we want to mark
  # the SeattleGENI user as unavailable for the future. Also we stamp it with
  # a new timestamp. Usually a resource expires in 4 hours, therefore we keep
  # track of the timestamp in order to calculate when the resource becomes 
  # available again.
  $protogeni_user_available{$auth_ref->{'username'}}->{'available'} = 0;
  $protogeni_user_available{$auth_ref->{'username'}}->{'time_acquired'} = time;
  $protogeni_user_available{$auth_ref->{'username'}}->{'api_key'} = $auth_ref->{'api_key'};

  return $server_call_result;
}





sub release_resources {

  # Extract the two arguments. Both the arguments are dictionaries and the format
  # is as follows:
  # %auth: {'username':'YOUR_USER_NAME', 'api_key':'YOUR_API_KEY'}
  # @handle_list: (LIST, WITH, ALL, THE, HANDLES, TO, RELEASE)

  my($auth_ref, $handle_list_ref) = @_;

  my $server = Frontier::Client->new('url' => $server_url);

  # Make the call on the server side to release all the resources for the user.    
  my $server_call_result = $server->call('release_resources', $auth_ref, $handle_list_ref);
  return $server_call_result;

}




sub setup_log_file() {
  # Setup and open up the log file in order for the logging system
  # to work properly. We want to ensure that the log file is open
  # by one call only, so the log doesn't become garbage.

  eval{
    open (LOGFILE, ">>", $log_filepath) or
      die "Can't open the file $log_filepath. Make sure the file exists and you have the right permissions";
    };
    if ($@) {
      print $@;
      print "Exiting program\n";
      exit(1);
    }

  # Maximum time to wait to acquire lock on log file.
  my $total_sleep = 0;
  
  while(!flock(LOGFILE, $LOCK_EX)){
    # Sleep for 0.1 sec, however dont' wait around for ever,
    # If we have slept more then 5 sec then just exit.
    sleep(0.1);
    $total_sleep += 0.1;

    if ($total_sleep > 3) {
      die "Could not acquire lock for $log_filepath.\nExiting program\n";
      exit(1);
    }
  }

}





sub printlog {
  # This is the logging system, we print out the message to the log file.
  my $log_message = shift(@_);
  my $error_code = shift(@_) || $NORMAL_LOG;

  # Retrieve the timestamp.
  my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime(time);

  # Convert the time to proper year and month. In perl year 0 is 1900 and 
  # month goes from 0-11.
  $year += 1900;
  $mon += 1;

  my $date = sprintf("%02d:%02d:%02d %02d-%02d-%4d", $hour, $min, $sec, $mday, $mon, $year);
  if ($error_code == $NORMAL_LOG) {
    print LOGFILE "$date: $log_message\n";
    #print "$date: $log_message\n";
  }
  elsif ($error_code == $ERROR_LOG) {
    print LOGFILE "$date ERROR: $log_message\n";
  }
}


# Call the main subroutine to get started.
main();




#
# Want to prevent bad exit.
#
END {

  my $exitcode = $?;

  # Close all files, which also releases the lock on them.
  close(USER_FILE);
  close(VESSELHANDLE_FILE);
  print LOGFILE "\n\n";
  close(LOGFILE);
  close(LOCKFILE);

  if ($exitcode) {
    my $decoder = Frontier::RPC2->new();
    print $decoder->encode_fault(-2, "XMLRPC Server Error");
    
  }
}
