<?php

if (isset($_POST)) {
	if ($_POST['action'] == 'adduser') {
		$username = standarize($_POST['username']);	
		$user = new User($username);
		
		if (is_uploaded_file($_FILES["publickey"]["tmp_name"])) {
			move_uploaded_file($_FILES["publickey"]["tmp_name"], "keys/" . $user->getName() . ".publickey");
			$user->setUploaded(true);
			$user->readPublicKey("keys/" . $user->getName() . ".publickey");
		} else {
			$user->setUploaded(false);
                        $user->generateKeys(); 
                        // NOTE: generateKeys already writes the key files
			//$user->writeKeys();
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
		Unset($vessel);
		
		$mypid = getmypid();
                $vesselinfopy = "/home/ivan/trunk/test/writecustominstallerinfo.py";
                $prefix = "/var/www/customized_installer";
                $dl_prefix = "$prefix/download";
                exec("rm -Rf $dl_prefix/* && mkdir $dl_prefix/vesselsinfo");
                file_put_contents("$dl_prefix/vesselsinfo_$mypid.txt", outputVesselsInfo($vessels));
                exec("python $vesselinfopy $dl_prefix/vesselsinfo_$mypid.txt $dl_prefix/vesselsinfo/");
                exec("python $prefix/customize_installers.py $dl_prefix/vesselsinfo seattle $dl_prefix/seattle");
                exec("cp $dl_prefix/seattle_linux.tgz $dl_prefix/seattle_mac.tgz");
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
        $prefix = "/var/www/customized_installer";
	return "$prefix/keys/" . $username . ".publickey";
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
                $prefix = "/var/www/customized_installer";
                // TODO: make keys directory unique to this session
                // NOTE: pids do not work here -- we need a **session** persistent unique id
                // $mypid = getmypid();
                // exec("mkdir $prefix/keys/$mypid/");
                
                // NOTE: this script already creates the public private key files
		// $keys = explode(" ", exec("python $prefix/generatekeys.py " . $this->name. " 512"));
                exec("python $prefix/generatekeys.py " . $this->name. " 128");
                //exec("mv $prefix/" . $this->name . ".publickey $prefix/keys/");
                //exec("mv $prefix/" . $this->name . ".privatekey $prefix/keys/");
		// $keys = array("dfajk22f3", "a23f3bc8");
		//$this->public_key = $keys[0];
		//$this->private_key = $keys[1];
	}
	
	public function writeKeys () {
		file_put_contents("keys/" . $this->name . ".publickey", $this->public_key);
		file_put_contents("keys/" . $this->name . ".privatekey", $this->private_key);
	}
	
	public function getPublicKey () {
		return $this->public_key;
	}
	
 
}


?>
