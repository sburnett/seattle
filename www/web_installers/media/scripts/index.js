//char limit: 17

var counter;
var vesselLengths = [1056, 0, 0, 0, 0, 0, 0, 0];
var vesselOwners = ["","","","","","","",""];
var vesselUsers = createArray();
var userTally = [0, 0, 0, 0, 0, 0, 0, 0];
var users = [];

function createArray() {
	var temp = new Array(8);
	for (i = 0; i < temp.length; ++i) {
		temp[i] = new Array(200);
	}
	return temp;
}

window.onload = function () {
	// counter for default usernames
	counter = 1;
	// add the user to the user box
	$("form").onsubmit = addUser;
	// guess the username from the given public key file
	$("publickey").onchange = updateUsername;
	// reset the form
	$("username").onfocus = function () {
		this.value = "";
	};
	$("username").onblur = function () {
		if (this.value === "") {
			this.value = "user_" + counter;
		}
	};
   	$("installer").disabled = true;
	Initialize();
	updateVessels();
	$("installer").onclick = createInstaller;
};

function removeelement() {
			var parent = this.parentNode.parentNode.parentNode;
			var subparent = this.parentNode.parentNode;
			if (subparent.id.substring(0, 5) == "owner") {
				var index = (Number)(parent.id[9]);
				var defaultNode = document.createElement("li");
				vesselOwners[index] = "";
				defaultNode.textContent = "Drag User Here to Create Owner";
				defaultNode.id = "owner" + index;
				parent.appendChild(defaultNode);
				subparent.remove();
			} else {
				var index = (Number)(parent.id[8]);
				var adds = $$(".addusers");
				//alert((parseInt(adds[index].style.height)));
				adds[index].style.height = (parseInt(adds[index].style.height) + 53) + "px";
				adds[index].style.lineHeight = (parseInt(adds[index].style.lineHeight) + 53) + "px";
				subparent.remove();
				vesselUsers[index][userTally[index]] = "";
				userTally[index]--;
				//fixheights(adds);
			}
}		
		
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
	this.style.display = "none";
	var index = (Number)((this.id)[6]+"");
	$("plus"+index).style.display = "block";
	var previousIndex = findNumberOfJumpsBack(index-1);
	vesselLengths[index-previousIndex] += vesselLengths[index];
	vesselLengths[index] = 0;
	updateVessels();
}

function addVessel() {
	this.style.display = "none";
	var index = (Number)((this.id)[4]+"");
	$("remove"+index).style.display = "block";
	var multiplier = findNumberOfJumps(index);
	vesselLengths[index] = (multiplier * 132) ;
	var previousIndex = findNumberOfJumpsBack(index-1);
	vesselLengths[index-previousIndex] -= (multiplier * 132);
	updateVessels();
	validate();
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
		owner.textContent = "Drag Owner Here";
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
		$("vessellist").appendChild(vessel);
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
		plus.style.top = ($("vessellist").offsetTop - 12) + "px";
		plus.textContent = "+";
		plus.id = "plus" + j;
		plus.onclick = addVessel;
		/*These try statements are used to make the website work on internet explorer, which doesn't support textContent*/
		try { if(!plus.innerText) plus.innerText = plus.textContent; } catch(e) {}
		plus.style.left = ((j * 132) + 8 ) + "px";
		$("pluses").appendChild(plus);
		var remove = document.createElement("p");
		remove.textContent = "X";
		try { if(!remove.innerText) remove.innerText = remove.textContent; } catch(e) {}
		remove.id = "remove" + j;
		remove.onclick = removeVessel;
		remove.style.display = "none";
		remove.style.width = "10px";
		remove.style.height = "10px";
		remove.style.position = "absolute";
		remove.style.left = ((j * 132) + 8 ) + "px";
		remove.style.top = ($("vessellist").offsetTop - 7) + "px";
		$("pluses").appendChild(remove);
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
		staticvessel.style.top = ($("vessellist").offsetTop); 
	} else {
		staticvessel.style.top = ($("vessellist").offsetTop);
	}
	staticvessel.style.marginTop = "15px";
	staticvessel.style.marginLeft = "1063px";
	staticvessel.style.border = "1px solid black";
	staticvessel.textContent = "2% Resources Reserved";
	staticvessel.style.fontSize = "18pt";
	staticvessel.style.backgroundColor = "Gray";
	try { if(!staticvessel.innerText) staticvessel.innerText = staticvessel.textContent; } catch(e) {}
	$("vessellist").appendChild(staticvessel);	
}

function addOwnerToList(draggable, droppable) {
	var index = (Number)(droppable.id[9]);
	$("owner" + index).remove();
	var newlyAdded = document.createElement("li");
	newlyAdded.id = "owner" + index;
	var length = draggable.textContent.length;
	var content = document.createElement("p");
	content.addClassName("container");
	content.textContent = (draggable.textContent.substring(0, length-1));
	vesselOwners[index] = (draggable.textContent.substring(0, length-1));
	try { if(!content.innerText) content.innerText = content.textContent; } catch(e) {}
	var link = document.createElement("a");
	link.addClassName("close");
	link.textContent = "X";
	link.onclick = removeelement;
	try { if(!link.innerText) link.innerText = link.textContent; } catch(e) {}
	content.appendChild(link);
	newlyAdded.appendChild(content);
	droppable.appendChild(newlyAdded);
	newlyAdded.addClassName("removable");
	validate();
}

function createAddUserBox(lastheight) {
	var user = document.createElement("li");
	user.textContent = "Drag Users Here";
	try { if(!user.innerText) user.innerText = user.textContent; } catch(e) {}
	user.addClassName("addusers");
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
	var link = document.createElement("a");
	link.addClassName("close");
	link.textContent = "X";
	link.onclick = removeelement;
	try { if(!link.innerText) link.innerText = link.textContent; } catch(e) {}
	var content = document.createElement("p");
	content.addClassName("container");
	var length = draggable.textContent.length;
	content.textContent = (draggable.textContent.substring(0, length-1));
	try { if(!content.innerText) content.innerText = content.textContent; } catch(e) {}
	content.appendChild(link);
	newlyAdded.appendChild(content);
	droppable.appendChild(newlyAdded);
	newlyAdded.addClassName("removable");
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
	vesselUsers[index][userTally[index]] = (draggable.textContent.substring(0, length-1));
	userTally[index]++;
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


/* add vessels to the user box */
function addUser () {
	if ($("username").value == "") {
		$("username").value = "user_" + counter;
	}
	var name = $("username").value;
	while (!name.match(/[\w_\-]+/)) {
		alert("Please enter usernames that only contain characters, digits, underscores and dashes.");
	}
	while (name.length > 20) {
		alert("Please enter usernames with maximum length of 20.");
	}
	if (name == "user_" + counter) {
		counter++;
	}
	if (users.indexOf(name) == -1) {
		users.push(name);
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
			$("plus" + i).style.top = ($("vessellist").offsetTop - 7) + "px";
			$("remove" + i).style.top = ($("vessellist").offsetTop - 2) + "px";
		}
	}
	
	new Ajax.Request('process.php',
		{
			method: "post",
			parameters: {action: "resetform", username: name},
			onSuccess: resetForm
		}
	);
}

/*  guess the username for given public key  */
function updateUsername () {
	if ($("publickey").value != "") {
		$("username").value = $("publickey").value.substring($("publickey").value.lastIndexOf("/") +1,
															 $("publickey").value.lastIndexOf("."));
	}
}

/*  automatically increment the username by one  */
function resetForm (ajax) {
	if (ajax.responseText == "custom") {
		$("username").value = "";
		$("publickey").value = "";
	} else {
		$("username").value = "user_" + counter;
		$("publickey").value = "";
	}
}


/*  create a json object that sends the vessel information to the server side  */
function createInstaller () {
	var json = [
		{
			"percentage": vesselLengths[0] / 132,
			"owner": vesselOwners[0],
		 	"users": vesselUsers[0]
		}, {
			"percentage": vesselLengths[1] / 132,
			"owner": vesselOwners[1],
			"users": vesselUsers[1]
		}, {
			"percentage": vesselLengths[2] / 132,
			"owner": vesselOwners[2],
			"users": vesselUsers[2]
		}, {
			"percentage": vesselLengths[3] / 132,
			"owner": vesselOwners[3],
			"users": vesselUsers[3]
		}, {
			"percentage": vesselLengths[4] / 132,
			"owner": vesselOwners[4],
			"users": vesselUsers[4]
		}, {
			"percentage": vesselLengths[5] / 132,
			"owner": vesselOwners[5],
			"users": vesselUsers[5]
		}, {
			"percentage": vesselLengths[6] / 132,
			"owner": vesselOwners[6],
			"users": vesselUsers[6]
		}, {
			"percentage": vesselLengths[7] / 132,
			"owner": vesselOwners[7],
			"users": vesselUsers[7]
		}
	];
	
	for (var i = 7; i >= 0; i--) {
		if (json[i].percentage == 0) {
			json.splice(i, 1);
		}
	}
	
	var jsonString =  Object.toJSON(json);
	new Ajax.Request('process.php',
		{
			method: "post",
			parameters: {action: "createinstaller", content: jsonString},
			onSuccess: finish
		}
	);
}

/*  redirect the page to installer download page  */
function finish (ajax) {
	location.href = "installers.php";
}


/*  check to make sure each vessel has at least a owner to generate the installer  */
function validate () {
	var valid = true;
	for (var i = 0; i < 7; i++) {
		if (vesselLengths[i] != 0 && vesselOwners[i] == "") {
			valid = false;
		}
	}
	if (valid) {
		$("installer").disabled = false;
	} else {
		$("installer").disabled = true;
	}
}


/*	Free online downloaded script that can return OS, Browser Name, and Browser Version,
	used for browser compatibility purposes*/
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

//This prototype is provided by the Mozilla foundation and
//is distributed under the MIT license.
//http://www.ibiblio.org/pub/Linux/LICENSES/mit.license

if (!Array.prototype.indexOf)
{
  Array.prototype.indexOf = function(elt /*, from*/)
  {
    var len = this.length;

    var from = Number(arguments[1]) || 0;
    from = (from < 0)
         ? Math.ceil(from)
         : Math.floor(from);
    if (from < 0)
      from += len;

    for (; from < len; from++)
    {
      if (from in this &&
          this[from] === elt)
        return from;
    }
    return -1;
  };
}