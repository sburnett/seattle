window.onload = function () {
	if ($("id_gen_upload_choice").lastChild.selected == "selected") {
		$("id_pubkey").style.display = "block";
	} else {
		$("id_pubkey").style.display = "none";
	}
	$("id_gen_upload_choice").lastChild.onselect = function() {
		$("id_pubkey").style.display = "block";
	}
	$("id_gen_upload_choice").firstChild.onselect = function() {
		$("id_pubkey").style.display = "none";
	}
};