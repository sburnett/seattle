var total = 0;
var totalallocatedunderfive = 0;
var totalusageunderfive = 0;
var totalnumbersofar = 0;

window.onload = function () {
	call();
	setInterval(call, 5000);
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
	var table2elementstoremove = $$(".addedtotable2");
	for (var j=0;j<table2elementstoremove.length;j++) {
		table2elementstoremove[j].remove();
	}
	var vessels = Ajax.responseText.split("\n");
	for (var i=1;i<=vessels.length;i++) {
		var vesselinfo = vessels[i-1].split(";");
		if (vesselinfo[2] < 5) {
			totalallocatedunderfive += (vesselinfo[2]*5);
			totalusageunderfive += (vesselinfo[3]*5);
			var newrow = document.createElement("tr");
			newrow.className = "addedtotable2";
			var newcolumn1 = document.createElement("td");
			var newcolumn2 = document.createElement("td");
			var newcolumn3 = document.createElement("td");
			newcolumn1.textContent = vesselinfo[0];
			newcolumn2.textContent = vesselinfo[2] + "%";
			newcolumn3.textContent = vesselinfo[3] + "%";
			newrow.appendChild(newcolumn1);
			newrow.appendChild(newcolumn2);
			newrow.appendChild(newcolumn3);
			$("toosmalltable").appendChild(newrow);
		} else {
			$("row" + i).style.display = "block";
			var vesselinfo = vessels[i-1].split(";");
			var currentHeight = (vesselinfo[2]*5)
			$("row" + i).style.height = currentHeight + "px";
			$("fill"+i).display = "none";
			$("fill" + i).style.paddingBottom = (vesselinfo[3]*5) + "px";
			$("text" + i).style.position = "absolute";
			$("text" + i).style.top = (total + (2*(totalnumbersofar-1)) + (currentHeight/2) + 5) + "px";
			$("text" + i).style.left = "0%";
			$("text" + i).style.right = "5%";
			total += currentHeight;
			totalnumbersofar++;
		}
	}
	if (totalallocatedunderfive > 0) {
		$("row20").style.display = "block";
	    $("row20").style.height = totalallocatedunderfive + 10 + "px";
		$("fill20").style.paddingBottom = totalusageunderfive + "px";
		$("text20").style.position = "absolute";
		$("text20").style.top = (total + (2*(totalnumbersofar-1)) + (totalallocatedunderfive/2) + 5) + "px";
		$("text20").style.left = "0%";
		$("text20").style.right = "5%";
	}
	totalusageunderfive = 0;
	totalallocatedunderfive = 0;
	total = 0;
    totalnumbersofar = 0;
}

function error() {
	alert("error");
}