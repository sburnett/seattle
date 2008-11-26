/*This is the javascript for the resourcemanager.html page.
Its main function is to properly handle the refreshing of the  
graphical representation of the vessels allocated and in use.
*/

var total = 0; //This keeps track of the total height in pixels, 
			   //its used to properly absolute position the Vessel Text "V1, V2, etc"
var totalallocatedunderfive = 0; //This keeps track of the number of vessels which have under 5% allocated
var totalusageunderfive = 0; //This keeps track of the total % in use by the vessels which have less than 5% allocated
var totalnumbersofar = 0; //This keeps track of the number of vessels which have been allocated to this point in time
var refreshrateinseconds = 5; //This specifies the refresh rate of the page in seconds (default is 5 seconds)
var vesselcolors = ["", "", "", "", ""];

//Onload, the page is refreshed once, and then sets up a timer which refreshes the page every 'refreshrateinseconds' seconds
window.onload = function () {
	call(); 
	setInterval(call, refreshrateinseconds * 1000);
};

//This function makes an ajax call to a file in the same directory called status which stores the data used by this webpage.
//Once the info is returned, the update method is called with this data.
function call() {
	new Ajax.Request("status", 
	{
		method: "get",
		onSuccess: update,
		onFailure: error
	});

}

/*This function handles all of the updating for the page, refreshing table data, and refreshing the graphical representations 
   of the vessels. 
*/
function update(Ajax) {
	//This loop rezeroes the vessel data in the graphical representation, to make the refreshing work properly
	for (var z = 1;z < 21;z++) {
		$("row" + z).style.display = "none";
		$("row" + z).style.height = "0px";
		$("row" + z).parentNode.style.display = "none";
		$("row" + z).parentNode.style.height = "0px";
	}
	
	//The following variable and loop rezero the data tables, to make refreshing work properly.
	var table2elementstoremove = $$(".addedtotable2");
	for (var j=0;j<table2elementstoremove.length;j++) {
		table2elementstoremove[j].remove();
	}
	
	//The 'vessels' variable  stores an array of vessels, with each element having a line of data about that particular vessel
	var vessels = Ajax.responseText.split("\n");
	
	//This loop handles the detailed elements of refreshing the page. It rebuilds the data tables, and rebuilds the graphical
	//representation of the allocated vessels
	for (var i=1;i<=vessels.length-1;i++) {
		var vesselinfo = vessels[i-1].split(","); //This variable stores the data for this particular vessel in an array
		//The next section populates the data tables by creating and appending new rows and columns
		var newinforow = document.createElement("tr");
		newinforow.className = "addedtotable2";
		var newinfocolumn1 = document.createElement("td");
		var newinfocolumn2 = document.createElement("td");
		newinfocolumn1.textContent = vesselinfo[0];
		newinfocolumn2.textContent = vesselinfo[1];
		newinforow.appendChild(newinfocolumn1);
		newinforow.appendChild(newinfocolumn2);
		$("keybody").appendChild(newinforow);
		//This if block handles the case of a vessel having less than 5% allocated to it, thus, populating the special table of vessels
		//with less than 5%, and tallying the global variables so that the <5% resources special vessel will come into existence later on in the code
		if (vesselinfo[2] < 5) {
			totalallocatedunderfive += Math.round(vesselinfo[2]*5);
			totalusageunderfive += Math.round(vesselinfo[3]*5);
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
			$("toosmallbody").appendChild(newrow);
		} else {
			//The next statements create the allocated table blocks
			$("row" + i).style.display = "block";
			$("row" + i).parentNode.style.display = "block";
			var vesselinfo = vessels[i-1].split(",");
			var currentHeight = Math.round(vesselinfo[2]*5);
			$("row" + i).style.height = currentHeight + "px";
			$("row" + i).parentNode.style.height = currentHeight + "px";
			//This statement creates the green status bar that shows the resources currently in use
			$("fill" + i).style.paddingBottom = (vesselinfo[3]*5) + "px";
			//The next 3 statements are used to absolutly position the Vessel Text (making it float over the shaded filling below.)
			$("text" + i).style.position = "absolute";
			$("text" + i).style.top = (total + (2*(totalnumbersofar-1)) + (currentHeight/2) + 5) + "px";
			$("text" + i).style.left = "42%";
			//This tallies the global variables, this is used to help absolute position the text above
			total += currentHeight;
			totalnumbersofar++;
		}
	}
	//This statement takes care of the single graphical block representing the vessels with less than 5% allocated.
	if (totalallocatedunderfive > 0) {
		$("row20").style.display = "block";
		$("row20").parentNode.style.display = "block";
	    $("row20").style.height = totalallocatedunderfive + 10 + "px";
		$("row20").parentNode.style.height = totalallocatedunderfive + 10 + "px";
		$("fill20").style.paddingBottom = totalusageunderfive + "px";
		$("text20").style.position = "absolute";
		$("text20").style.top = (total + (2*(totalnumbersofar-1)) + (totalallocatedunderfive/2) + 5) + "px";
		$("text20").style.left = "9";
	}
	//The following statements rezero the global variables 
	totalusageunderfive = 0;
	totalallocatedunderfive = 0;
	total = 0;
    totalnumbersofar = 0;
}

//Prints an error message if the ajax call fails
function error() {
	alert("error");
}