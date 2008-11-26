<?php

session_start();
// echo session_id() ;
echo $_SESSION['count'];

$prefix = "/var/www/customized_installer";
$carter_script = "/home/ivan/trunk/dist/customize_installers.py";
$vesselinfopy = "/home/ivan/trunk/test/writecustominstallerinfo.py";
$sid = session_id();
$dl_prefix = "$prefix/download/$sid";

if (isset($_POST)) {
	if ($_POST['action'] == 'adduser') {
		$username = standarize($_POST['username']);
                if (is_uploaded_file($_FILES["publickey"]["tmp_name"])) {
			$key = file_get_contents($_FILES["publickey"]["tmp_name"]);
			$_SESSION[$username] = $key;
		} else {
			unset($_SESSION[$username]);
		}
		// echo $_SESSION[$username];
	} else if ($_POST['action'] == 'createinstaller') {
		$vessels = json_decode(stripslashes($_POST['content']), true);
		exec("rm $dl_prefix/*");
		exec("mkdir $dl_prefix");
		exec("mkdir $dl_prefix/vesselsinfo");
		//file_put_contents("h0","");
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
		//file_put_contents("h1","");
                file_put_contents("$dl_prefix/vesselsinfo.txt", outputVesselsInfo($vessels));
		//file_put_contents("h2","");
                exec("python $vesselinfopy $dl_prefix/vesselsinfo.txt $dl_prefix/vesselsinfo/");
		//file_put_contents("h3","");
                exec("cd $dl_prefix/tmp/ && python $carter_script mlw $dl_prefix/vesselsinfo $dl_prefix/ > /tmp/carter.out.php 2> /tmp/carter.err.php");
		//file_put_contents("h4","");
		exec("zip -j $dl_prefix/private.zip $dl_prefix/*.privatekey");
		//file_put_contents("h5","");
		exec("zip -j $dl_prefix/public.zip $dl_prefix/*.publickey");
		//file_put_contents("h6","");
                //exec("cp $dl_prefix/seattle_linux.tgz $dl_prefix/seattle_mac.tgz");
	}
	 /* else if ($_POST['action'] == 'resetform') { */
/* 		$username = standarize($_POST['username']); */
/* 		if (file_exists(getPublicKeyPath($username)) && !preg_match("/^user_\d$/", $username)) { */
/* 			echo "custom"; */
/* 		} */
/* 	} */
}

function genkey($user) {
	global $prefix, $dl_prefix;
	if (array_key_exists($user, $_SESSION)) {
		file_put_contents(getPublicKeyPath($user), $_SESSION[$user]);
	} else {
		exec("python $prefix/generatekeys.py $user 128 $dl_prefix/");
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
	global $dl_prefix;
	return "$dl_prefix/" . $username . ".publickey";
}

?>
