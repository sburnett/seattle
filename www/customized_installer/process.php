<?php

if (isset($_POST)) {
	if ($_POST['action'] == 'adduser') {
		$username = standarize($_POST['username']);	
		$user = new User($username);
		
		if (is_uploaded_file($_FILES["publickey"]["tmp_name"])) {
			move_uploaded_file($_FILES["publickey"]["tmp_name"], "keys/" . $user->getName() . ".public");
			$user->setUploaded(true);
			$user->readPublicKey("keys/" . $user->getName() . ".public");
		
		} else {
			$user->setUploaded(false);
			$user->generateKeys();
			$user->writeKeys();
		}
		// echo $user->getName() . " is added.";
	} else if ($_POST['action'] == 'createinstaller') {
		$vessels = json_decode(stripslashes($_POST['content']), true);
		foreach ($vessels as &$vessel) {
			$vessel['owner'] = getPublicKeyPath(standarize($vessel['owner']));
			foreach ($vessel['users'] as &$user) {
				$user = getPublicKeyPath(standarize($user));
			}
			unset($user);
		}
		unset($vessel);
		$mypid = getmypid();
                $vesselinfopy = "/home/ivan/trunk/test/writecustominstallerinfo.py"
                $prefix = "/var/www/customized_installer/download"
                exec("mkdir $prefix/$mypid");
                file_put_contents("$prefix/vesselsinfo_$mypid.txt", outputVesselsInfo($vessels)); 
                exec("python $vesselinfopy $prefix/vesselsinfo_$mypid.txt $prefix/$mypid/")
	} else if ($_POST['action'] == 'resetform') {
		$username = standarize($_POST['username']);
		if (file_exists(getPublicKeyPath($username)) && !preg_match("/^user_\d$/", $username)) {
			echo "custom";
		}
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
	return "keys/" . $username . ".public";
}

class User {

	private $name;
	private $public_key;
	private $private_key;
	private $key_uploaded;

	public function __construct ($name) {
		$this->name = $name;
		$this->public_key = "";
		$this->private_key = "";
		$this->key_uploaded = false;
	}
	
	public function setUploaded ($uploaded) {
		$this->key_uploaded = $uploaded;
	}
	
	public function getName () {
		return $this->name;
	}
	
	public function readPublicKey ($file) {
		$this->public_key = trim(file_get_contents($file));
		$this->private_key = "";
	}
	
	public function generateKeys () {
		// $keys = explode(" ", exec("keygen.py"));
		// !!this line needs to be replaced
		$keys = array("dfajk22f3", "a23f3bc8");
		$this->public_key = $keys[0];
		$this->private_key = $keys[1];
	}
	
	public function writeKeys () {
		file_put_contents("keys/" . $this->name . ".public", $this->public_key);
		file_put_contents("keys/" . $this->name . ".private", $this->private_key);
	}
	
	public function getPublicKey () {
		return $this->public_key;
	}
	
 
}


?>
