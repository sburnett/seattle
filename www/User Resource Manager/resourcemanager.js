


window.onload = function () {
	call();
};

function call() {
	new Ajax.Request("status", 
	{
		method: "get",
		onSuccess: update,
		onFailure: error
	});

}

function update(Ajax) {
	var vessels = Ajax.responseText.split("\n");
	for (var i=1;i<=vessels.length;i++) {
		$("row" + i).style.display = "block";
		var vesselinfo = vessels[i-1].split(";");
		$("row" + i).style.height = vesselinfo[2] + "%";
		$("fill" + i).style.paddingBottom = vesselinfo[3] + "%";
		$("text" + i).style.position = "absolute";
		//$("text" + i).style.top = (2*i) + "%";
	}
}

function error() {
	alert("error");
}