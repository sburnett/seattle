window.onload = function () {
	var platform = detectOS();
	switch (platform) {
		case "win":
			$("win").addClassName("highlight");
			break;
		case "mac":
			$("mac").addClassName("highlight");
			break;
		case "linux":
			$("linux").addClassName("highlight");
			break;
		default:
			break;
	}
}

function detectOS () {
	var platform;
	if (navigator.platform.match(/win/i)) {
		platform = "win";
	} else if (navigator.platform.match(/mac/i)) {
		platform = "mac";
	} else if (navigator.platform.match(/linux/i)) {
		platform = "linux";
	} else {
		platform = "unknown";
	}
	return platform;
}