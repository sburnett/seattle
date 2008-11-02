window.onload = function () {
	if ($("id_gen_upload_choice").lastChild.selected == "selected") {
		$("id_pubkey").style.display = "block";
	} else {
		$("id_pubkey").style.display = "none";
	}
	$("id_gen_upload_choice").onchange = function() {
		if (this.value == "1") {
			$("id_pubkey").style.display = "none";
		} else {
			$("id_pubkey").style.display = "block";
		}
	}
};