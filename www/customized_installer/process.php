<?php

session_start();
echo session_id() ;
echo $_SESSION['count'];

$prefix = "/var/www/customized_installer";
$vesselinfopy = "/home/ivan/trunk/test/writecustominstallerinfo.py";
$sid = session_id();
$dl_prefix = "$prefix/download/$sid";

if (!isset($_SESSION['keys'])) {
	$_SESSION['keys'] = array();
}
// print $sid . "\n";
// echo $_SESSION['keys'];
    
if (isset($_POST)) {
	if ($_POST['action'] == 'adduser') {
		$username = standarize($_POST['username']);
		$key = file_get_contents($_FILES["publickey"]["tmp_name"]);
		$_SESSION['keys'][$username] = $key;
		echo $_SESSION['keys'][$username];

	} else if ($_POST['action'] == 'createinstaller') {
		$vessels = json_decode(stripslashes($_POST['content']), true);
		exec("rm $dl_prefix/* && mkdir $dl_prefix && mkdir $dl_prefix/vesselsinfo");
		
		foreach ($vessels as &$vessel) {
			genkey($vessel['owner']);
			$vessel['owner'] = getPublicKeyPath(standarize($vessel['owner']));
			
			foreach ($vessel['users'] as &$user) {
				genkey($user);
				$user = getPublicKeyPath(standarize($user));
			}
			unset($user);
		}
		Unset($vessel);
		
                file_put_contents("$dl_prefix/vesselsinfo.txt", outputVesselsInfo($vessels));

                exec("python $vesselinfopy $dl_prefix/vesselsinfo.txt $dl_prefix/vesselsinfo/");
                exec("python $prefix/customize_installers.py mlw $dl_prefix/vesselsinfo $dl_prefix/");
                exec("cp $dl_prefix/seattle_linux.tgz $dl_prefix/seattle_mac.tgz");
	}
	 /* else if ($_POST['action'] == 'resetform') { */
/* 		$username = standarize($_POST['username']); */
/* 		if (file_exists(getPublicKeyPath($username)) && !preg_match("/^user_\d$/", $username)) { */
/* 			echo "custom"; */
/* 		} */
/* 	} */
}

function genkey($user) {
	if (!isset($_SESSION['keys'][$user])) {
		exec("python $prefix/generatekeys.py $user 128 $dl_prefix/");
	} else {
		file_put_contents("$dl_prefix/" . $user . ".privatekey" , $_SESSION['keys'][$user]);
	}
}

function outputVesselsInfo ($vessels) {
	$output = '';
	foreach ($vessels as $vessel) {
		$output .= "Percent " . $vessel['percentage'] . "\n";
		$output .= "Owner " . $vessel['owner'] . "\n";
		foreach ($vessel['users'] as $user) {
			$output .= "User " . $user . "\n";
		}
	}
	return $output;
}

function standarize ($username) {
	return preg_replace("/\s/", "_", strtolower(trim($username)));
}

function getPublicKeyPath ($username) {
        $prefix = "/var/www/customized_installer";
	return "$prefix/keys/" . $username . ".publickey";
}

?>
