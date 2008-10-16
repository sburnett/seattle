<?php

if (isset($_POST)) {
	if ($_POST['action'] == 'adduser') {
		$username = $_POST['username'];
		$user = new User($username);
		
		if (is_uploaded_file($_FILES["publickey"]["tmp_name"])) {
			move_uploaded_file($_FILES["publickey"]["tmp_name"], "uploaded_keys/" . $user->getName() . ".txt");
			$user->setUploaded(true);
			$user->readPublicKey("uploaded_keys/" . $user->getName() . ".txt");
		
		} else {
			$user->setUploaded(false);
			$user->generateKeys();
		}
		echo $user->getName() . " is added. private key is " . $user->getPrivateKey() ;
	}
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
		$keys = array("public_dfajk22f3", "private_23f3bc8");
		$this->public_key = $keys[0];
		$this->private_key = $keys[1];
	}
	
	public function getPublicKey () {
		return $this->public_key;
	}
	
	public function getPrivateKey () {
		return $this->private_key;
	}
 
}


?>