
$(document).ready(function() {
	$("#id_gen_upload_choice").chnage(toggle_upload);
});

function toggle_upload() {
	if ($("#id_gen_upload_choice").val() == "1") {
		$("#uploadkey").hide();
	} else {
		$("#uploadkey").show();
	}
}
