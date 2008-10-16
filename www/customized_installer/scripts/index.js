var counter;
vesselLengths = [1056, 0, 0, 0, 0, 0, 0, 0]
vesselOwners = ["","","","","","","",""]
vessel1Users = []
vessel2Users = []
vessel3Users = []
vessel4Users = []
vessel5Users = []
vessel6Users = []
vessel7Users = []
vessel8Users = []

window.onload = function () {
	counter = 1;
	$("form").onsubmit = addUser;
	$("username").onfocus = function () {
		this.value = "";
	}
	$("username").onblur = function () {
		if (this.value == "") {
			this.value = "user_" + counter;
		}
	}
	Initialize();
	updateVessels();
	Droppables.add("content", {
		accept: "removable",
		onDrop: function(draggable) {
			var parent = draggable.parentNode;
			var index = (Number)(parent.id[8]);
			if (draggable.id.substring(0, 4) == "owner") {
				var defaultNode = document.createElement("li");
				defaultNode.textContent = "Add Owner";
				defaultNode.id = "owner" + index;
				parent.appendChild(defaultNode);
				draggable.remove();
			} else {
				var adds = $$(".addusers");
				//alert((parseInt(adds[index].style.height)));
				adds[index].style.height = (parseInt(adds[index].style.height) + 53) + "px";
				adds[index].style.lineHeight = (parseInt(adds[index].style.lineHeight) + 53) + "px";
				draggable.remove();
				//fixheights(adds);
			}	
			
		}
	});
};

function fixheights(adds) {
	var test = true;
	for (var i = 0;i < adds.length;i++) {
		if ((parseInt(adds[index].style.height)) < 53) {
			test = false;
		}
	}
	if (test) {
		for (var j = 0;j < adds.length;j++) {
			adds[j].style.height = (parseInt(adds[index].style.height) - 53) + "px";
			adds[j].style.lineHeight = (parseInt(adds[index].style.lineHeight) - 53) + "px";
		}	
	}
	
}

function removeVessel() {
	new Effect.Fade(this);
	var index = (Number)((this.id)[6]+"");
	new Effect.Appear($("plus"+index));
	var previousIndex = findNumberOfJumpsBack(index-1);
	vesselLengths[index-previousIndex] += vesselLengths[index];
	vesselLengths[index] = 0;
	updateVessels();
}

function addVessel() {
	new Effect.Fade(this);
	var index = (Number)((this.id)[4]+"");
	new Effect.Appear($("remove"+index));
	var multiplier = findNumberOfJumps(index);
	vesselLengths[index] = (multiplier * 132) ;
	var previousIndex = findNumberOfJumpsBack(index-1);
	vesselLengths[index-previousIndex] -= (multiplier * 132);
	updateVessels();
}

function findNumberOfJumpsBack(index) {
	var total = 1;
	for (var i = index;i >= 0;i--) {
		if (vesselLengths[i] > 0) {
			return total;
		}
		total++;
	}
	return total;
}

function findNumberOfJumps(index) {
	var total = 0;
	for (var i = index;i < 8;i++) {
		if (vesselLengths[i] > 0) {
			return total;
		} 
		total++;
	}
	return total;
}

function Initialize() {
/* Initializes the Vessels, including their remove button */
	for (var i = 0;i < 8;i++) {
		var vessel = document.createElement("div");
		vessel.style.left = ((132 * i) + 7) + "px";//" 6 138 270
		vessel.id = "vessel" + i;
		vessel.addClassName("vessel");
		var ownerlist = document.createElement("ul");
		ownerlist.id = "ownerlist" + i;
		ownerlist.className = "ownerlist";
		var ownerheader = document.createElement("li");
		ownerheader.textContent = "Owner";
		ownerheader.addClassName("ownerheader");
		try { if(!ownerheader.innerText) ownerheader.innerText = ownerheader.textContent; } catch(e) {}
		var owner = document.createElement("li");
		owner.textContent = "Add Owner";
		owner.id = "owner" + i;
		try { if(!owner.innerText) owner.innerText = owner.textContent; } catch(e) {}
		var userlist = document.createElement("ul");
		userlist.id = "userlist" + i;
		userlist.className = "userlist";
		var userheader = document.createElement("li");
		userheader.textContent = "Users";
		userheader.addClassName("ownerheader");
		try { if(!userheader.innerText) userheader.innerText = userheader.textContent; } catch(e) {}
		var user = createAddUserBox("50");
		ownerlist.appendChild(ownerheader);
		ownerlist.appendChild(owner);
		userlist.appendChild(userheader);
		userlist.appendChild(user);
		vessel.appendChild(ownerlist);
		vessel.appendChild(userlist);
		$("VesselList").appendChild(vessel);
		Droppables.add(ownerlist.id, {
			accept: "user",
			onDrop: addOwnerToList
		});
		Droppables.add(userlist.id, {
			accept: "user",
			onDrop: addUserToList
		});
	}
	/*Initializes the plus signs and remove buttons*/
	for (var j = 1;j < 8;j++) {
		var plus = document.createElement("p");
		plus.style.width = "10px";
		plus.style.position = "absolute";
		plus.style.height = "10px";
		plus.style.fontWeight = "Bold";
		plus.style.fontSize = "11pt";
		plus.style.top = ($("VesselList").offsetTop - 12) + "px";
		plus.textContent = "+";
		plus.id = "plus" + j;
		plus.onclick = addVessel;
		/*These try statements are used to make the website work on internet explorer, which doesn't support textContent*/
		try { if(!plus.innerText) plus.innerText = plus.textContent; } catch(e) {}
		plus.style.left = ((j * 132) + 1 ) + "px";
		$("Pluses").appendChild(plus);
		var remove = document.createElement("p");
		remove.textContent = "X";
		try { if(!remove.innerText) remove.innerText = remove.textContent; } catch(e) {}
		remove.id = "remove" + j;
		remove.onclick = removeVessel;
		remove.style.display = "none";
		remove.style.width = "10px";
		remove.style.height = "10px";
		remove.style.position = "absolute";
		remove.style.left = ((j * 132) + 4 ) + "px";
		remove.style.top = ($("VesselList").offsetTop - 7) + "px";
		$("Pluses").appendChild(remove);
	}
	/*Initializes the untouchable "2%" vessel block*/
	var staticvessel = document.createElement("span");
	staticvessel.id = "staticvessel";
	staticvessel.style.display = "inline-block";
	staticvessel.style.width = "192px";
	staticvessel.style.height = "172px";
	staticvessel.style.position = "absolute";
	staticvessel.style.textAlign = "center";
	if (BrowserDetect.browser == "Explorer") {
		staticvessel.style.top = "354px";
	} else {
		staticvessel.style.top = "349px";
	}
	staticvessel.style.left = "1063px";
	staticvessel.style.border = "1px solid black";
	staticvessel.textContent = "2% Resources Reserved";
	staticvessel.style.fontSize = "18pt";
	staticvessel.style.backgroundColor = "Gray";
	try { if(!staticvessel.innerText) staticvessel.innerText = staticvessel.textContent; } catch(e) {}
	$("content").appendChild(staticvessel);	
}

function addOwnerToList(draggable, droppable) {
	var index = (Number)(droppable.id[9]);
	$("owner" + index).remove();
	var newlyAdded = document.createElement("li");
	newlyAdded.id = "owner" + index;
	var length = draggable.textContent.length;
	newlyAdded.textContent = (draggable.textContent.substring(0, length-1));
	vesselOwners[index] = (draggable.textContent.substring(0, length-1));
	try { if(!newlyAdded.innerText) newlyAdded.innerText = newlyAdded.textContent; } catch(e) {}
	droppable.appendChild(newlyAdded);
	newlyAdded.addClassName("removable");
	new Draggable(newlyAdded, {revert: true, ghosting: true});
}

function createAddUserBox(lastheight) {
	var user = document.createElement("li");
	user.textContent = "Drag Users Here To Add";
	try { if(!user.innerText) user.innerText = user.textContent; } catch(e) {}
	user.className = "addusers";
	if (lastheight < 53) {
		user.style.height = "50px";
		user.style.lineHeight = "50px";
	} else {
		user.style.height = (lastheight-53) + "px";
		user.style.lineHeight = (lastheight-53) + "px";
	}
	return user;
}

function addUserToList(draggable, droppable) {
	var index = (Number)(droppable.id[8]);
	var lastheight = parseInt(droppable.lastChild.style.height);
	droppable.lastChild.remove();
	var newlyAdded = document.createElement("li");
	if ($("user" + index + "-1")) {
		var lastchildID = droppable.lastChild.id
		newlyAdded.id = "user" + index + "-" + ((Number)(lastchildID.substring(6, lastchildID.length)) + 1);
	} else {
		newlyAdded.id = "user" + index + "-1";
	}
	var length = draggable.textContent.length;
	newlyAdded.textContent = (draggable.textContent.substring(0, length-1));
	try { if(!newlyAdded.innerText) newlyAdded.innerText = newlyAdded.textContent; } catch(e) {}
	droppable.appendChild(newlyAdded);
	newlyAdded.addClassName("removable");
	new Draggable(newlyAdded, {revert: true, ghosting: true});
	var adds = $$(".addusers");
	if (lastheight < 53) {
		for (var i = 0;i < adds.length;i++) {
			adds[i].style.height = (parseInt(adds[i].style.height) + 53) + "px";	
			adds[i].style.lineHeight = (parseInt(adds[i].style.lineHeight) + 53) + "px";
		}
		$("staticvessel").style.height = (parseInt($("staticvessel").style.height) + 53) + "px";
	}
	var vessels = $$(".vessel");
	var addBox = createAddUserBox(lastheight);
	droppable.appendChild(addBox);	
}

function updateVessels() {
	for (var i = 0;i < vesselLengths.length;i++) {
		if (vesselLengths[i] > 0) {
			$(("vessel" + i)).style.display = "inline";
			$(("vessel" + i)).style.width = vesselLengths[i] + "px";
		} else {
			$("vessel" + i).style.display = "none";
		}
	}
}

function addUser () {
	// $("publickey").value = "";
	if ($("username").value == "") {
		$("username").value = "user_" + counter;
	}
	var name = $("username").value;
	if (name == "user_" + counter) {
		counter++;
	}
	// $("username").value = "user_" + counter;
	
	var user = document.createElement("span");
	var close = document.createElement("a");
	user.addClassName("user");
	user.id = name;
	user.textContent = name;
	close.textContent = "x";
	close.addClassName("close");
	close.href = "#";
	close.onclick = function () {
		// new Effect.Squish(name);
		$("names").removeChild(user);
	};
	user.appendChild(close);
	$("names").appendChild(user);
	new Draggable(name, {revert: true, ghosting: true});
	for (var i = 1;i < 8;i++) {
		$("plus" + i).style.top = ($("VesselList").offsetTop - 7) + "px";
		$("remove" + i).style.top = ($("VesselList").offsetTop - 2) + "px";
	}
	if (BrowserDetect.browser == "Explorer") {
		$("staticvessel").style.top = ($("VesselList").offsetTop + 20) + "px";
	} else { 5
		$("staticvessel").style.top = ($("VesselList").offsetTop + 15) + "px";
	}
}


function resetForm (event) {
	$("publickey").value = "";
	$("username").value = "user_" + counter;
}


/*Free online downloaded script that can return OS, Browser Name, and Browser Version, used for browser compatibility purposes*/
var BrowserDetect = {
	init: function () {
		this.browser = this.searchString(this.dataBrowser) || "An unknown browser";
		this.version = this.searchVersion(navigator.userAgent)
			|| this.searchVersion(navigator.appVersion)
			|| "an unknown version";
		this.OS = this.searchString(this.dataOS) || "an unknown OS";
	},
	searchString: function (data) {
		for (var i=0;i<data.length;i++)	{
			var dataString = data[i].string;
			var dataProp = data[i].prop;
			this.versionSearchString = data[i].versionSearch || data[i].identity;
			if (dataString) {
				if (dataString.indexOf(data[i].subString) != -1)
					return data[i].identity;
			}
			else if (dataProp)
				return data[i].identity;
		}
	},
	searchVersion: function (dataString) {
		var index = dataString.indexOf(this.versionSearchString);
		if (index == -1) return;
		return parseFloat(dataString.substring(index+this.versionSearchString.length+1));
	},
	dataBrowser: [
		{
			string: navigator.userAgent,
			subString: "Chrome",
			identity: "Chrome"
		},
		{ 	string: navigator.userAgent,
			subString: "OmniWeb",
			versionSearch: "OmniWeb/",
			identity: "OmniWeb"
		},
		{
			string: navigator.vendor,
			subString: "Apple",
			identity: "Safari"
		},
		{
			prop: window.opera,
			identity: "Opera"
		},
		{
			string: navigator.vendor,
			subString: "iCab",
			identity: "iCab"
		},
		{
			string: navigator.vendor,
			subString: "KDE",
			identity: "Konqueror"
		},
		{
			string: navigator.userAgent,
			subString: "Firefox",
			identity: "Firefox"
		},
		{
			string: navigator.vendor,
			subString: "Camino",
			identity: "Camino"
		},
		{		// for newer Netscapes (6+)
			string: navigator.userAgent,
			subString: "Netscape",
			identity: "Netscape"
		},
		{
			string: navigator.userAgent,
			subString: "MSIE",
			identity: "Explorer",
			versionSearch: "MSIE"
		},
		{
			string: navigator.userAgent,
			subString: "Gecko",
			identity: "Mozilla",
			versionSearch: "rv"
		},
		{ 		// for older Netscapes (4-)
			string: navigator.userAgent,
			subString: "Mozilla",
			identity: "Netscape",
			versionSearch: "Mozilla"
		}
	],
	dataOS : [
		{
			string: navigator.platform,
			subString: "Win",
			identity: "Windows"
		},
		{
			string: navigator.platform,
			subString: "Mac",
			identity: "Mac"
		},
		{
			string: navigator.platform,
			subString: "Linux",
			identity: "Linux"
		}
	]

};
BrowserDetect.init();