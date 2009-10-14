//char limit: 17

var counter;
var vesselLengths = [1056, 0, 0, 0, 0, 0, 0, 0];
var vesselOwners = ["","","","","","","",""];
var vesselUsers = createArray();
var userTally = [0, 0, 0, 0, 0, 0, 0, 0];
var activeusers = [];

function createArray() {
	var temp = new Array(8);
	for (i = 0; i < temp.length; ++i) {
		temp[i] = new Array(200);
	}
	return temp;
}

window.onload = function () {
  
  checkIfNewSession();

	// counter for default usernames
	counter = 1;
	// add the user to the user box
	$("form").onsubmit = pre_addUser;
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

  // reset the POST response form! 
  // (so it wont trigger the POST handler)
  window.frames['target'].document.body.innerHTML = "";
  
  // reset the users array
  var activeusers = [];
  
	Initialize();
	updateVessels();
	resetForm();
	$("installer").onclick = createInstaller;
	$("debugbutton").onclick = debug;

	var POST_frame = document.getElementById('target')
	if (POST_frame.addEventListener) {
	  POST_frame.addEventListener("load", add_post_handler, false)
	} else if (POST_frame.attachEvent) {
    POST_frame.detachEvent("onload", add_post_handler)
	  POST_frame.attachEvent("onload", add_post_handler)
	}

	add_post_handler();
};

function debug() {
  debugtext = "vesselOwners: " + vesselOwners.join(" ");
  debugtext += "<br>vesselUsers: " + vesselUsers.join(" ");
  
  document.getElementById("debug").innerHTML = debugtext;
  changeTextById("debug", debugtext);
}


// This function is called whenever a POST request completes 
// (originating from the 'target' iframe), and performs actions based
// on the POST response that the server gives. (eg: Alert the user about
// a bad pubkey, reenable the Add User button, etc...)
function add_post_handler() {
  post_response = window.frames['target'].document.body.innerHTML;
  split_response = post_response.split("_");
  
  if(split_response[0] == "done") {
    addUser();
  
  } else if (split_response[0] == "usernameempty") {
    alert("Please enter a username.");
    resetForm();
  
  } else if (split_response[0] == "usernamebad") {
    alert("You entered an invalid username.");
    resetForm();
  
  } else if (split_response[0] == "duplicateusername") {
    alert("The username you entered already exists!");
    resetForm();
    
  } else if (split_response[0] == "pubkeytoolarge") {
    alert("The public key you uploaded was too large! The filesize limit is " + split_response[1] + " bytes.");
    resetForm();
    
  } else if (split_response[0] == "pubkeybad") {
    alert("The public key you uploaded was invalid. Please try again.");
    resetForm();
    
  }
}


function checkIfNewSession() {
	new Ajax.Request('/html/check_session',
		{
			method: "post",
			parameters: {action: "checksession"},
			onSuccess: refreshIfNewSession,
			onFailure: checkIfNewSession_fail
		}
	);
}


function refreshIfNewSession(ajax) {
  if (ajax.responseText == "need_refresh") {
    location.href = "/html/installer_creator";
  }
}


function checkIfNewSession_fail(ajax) {
  document.write("Ajax call checkIfNewSession() failed. Please contact us!");
}


function removeelement(elem) {
			var parent = elem.parentNode.parentNode.parentNode;
			var subparent = elem.parentNode.parentNode;
			if (subparent.id.substring(0, 5) == "owner") {
				var index = (Number)(parent.id.charAt(9));
				var defaultNode = document.createElement("li");
				Element.extend(defaultNode);
				
				vesselOwners[index] = "";
				changeTextById(defaultNode, "Drag Owner Here");
				
				defaultNode.id = "owner" + index;
				parent.appendChild(defaultNode);
				subparent.remove();

				
			} else {
				var index = (Number)(parent.id.charAt(8));
				var adds = $$(".addusers");
				//alert((parseInt(adds[index].style.height)));
				adds[index].style.height = (parseInt(adds[index].style.height) + 53) + "px";
				adds[index].style.lineHeight = (parseInt(adds[index].style.lineHeight) + 53) + "px";
				subparent.remove();
				
				var username;
				var length;
				if (supportsInnerText()) {
          length = elem.parentNode.innerText.length;
          username = elem.parentNode.innerText.substring(0, length-1);
        } else {
				  length = elem.parentNode.textContent.length;
				  username = elem.parentNode.textContent.substring(0, length-1);
				}
				to_remove_idx = vesselUsers[index].indexOf(username);
				vesselUsers[index].splice(to_remove_idx, 1);
				
				//alert("userTally: " + userTally + "\n" + "vesselUsers[" + index+ "][userTally[" + index +"]]: " + vesselUsers[index][userTally[index]]);
				//vesselUsers[index][userTally[index]] = "";
				userTally[index]--;
				
				//fixheights(adds);
			}
			validate();
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
	var index = (Number)(this.id.charAt(6)+"");
	
	// remove users
	userlist = document.getElementById("userlist" + index);
	user_li_list = userlist.getElementsByTagName('li');
	
	for (var i=user_li_list.length-1; i>0; i--) {
    if (supportsInnerText()) {
      text = user_li_list[i].innerText; 
    } else {
	    text = user_li_list[i].textContent;
	  }
    
    if (text.substring(text.length-1, text.length) == 'X') {
      link = user_li_list[i].childNodes[0].childNodes[1];
      removeelement(link);
    }
    
  }
	
	// remove owners
	link = document.getElementById("ownerlist" + index).childNodes[1].childNodes[0].childNodes[1];
	if (link != null) {
	  removeelement(link);
	}
	
	$("plus"+index).style.display = "block";
	var previousIndex = findNumberOfJumpsBack(index-1);
	vesselLengths[index-previousIndex] += vesselLengths[index];
	vesselLengths[index] = 0;
	updateVessels();
	validate();
}

function addVessel() {
	this.style.display = "none";
	var index = (Number)(this.id.charAt(4)+"");
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
		Element.extend(vessel);
		
		vessel.style.left = ((132 * i) + 7) + "px";
		vessel.id = "vessel" + i;
		vessel.addClassName("vessel");
		var ownerlist = document.createElement("ul");
		Element.extend(ownerlist);
		
		ownerlist.id = "ownerlist" + i;
		ownerlist.className = "ownerlist";
		var ownerheader = document.createElement("li");
		Element.extend(ownerheader);
		
		ownerheader.textContent = "Owner";
		ownerheader.addClassName("ownerheader");
		try { if(!ownerheader.innerText) ownerheader.innerText = ownerheader.textContent; } catch(e) {}
		var owner = document.createElement("li");
		Element.extend(owner);
		
		owner.textContent = "Drag Owner Here";
		owner.id = "owner" + i;
		try { if(!owner.innerText) owner.innerText = owner.textContent; } catch(e) {}
		var userlist = document.createElement("ul");
		Element.extend(userlist);
		
		userlist.id = "userlist" + i;
		userlist.className = "userlist";
		var userheader = document.createElement("li");
		Element.extend(userheader);
		
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
		Element.extend(plus);
		
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
		Element.extend(remove);
		
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
	Element.extend(staticvessel);
	
	staticvessel.id = "staticvessel";
	staticvessel.style.display = "inline-block";
	staticvessel.style.width = "192px";
	staticvessel.style.height = "172px";
	staticvessel.style.position = "absolute";
	staticvessel.style.textAlign = "center";
	if (BrowserDetect.browser == "Explorer") {
		//staticvessel.style.top = ($("vessellist").offsetTop); 
	} else {
		//staticvessel.style.top = ($("vessellist").offsetTop);
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
	
	var index = (Number)(droppable.id.charAt(9));
	$("owner" + index).remove();
	var newlyAdded = document.createElement("li");
	Element.extend(newlyAdded);
	
	newlyAdded.id = "owner" + index;
	
	if (supportsInnerText()) { var length = draggable.innerText.length; } else { var length = draggable.textContent.length; }
	
	var content = document.createElement("p");
	Element.extend(content);
	
	content.addClassName("container");
	
	var username = "";
	if (supportsInnerText()) {
    username = (draggable.innerText.substring(0, length-1));
    content.innerText = username;
  } else {
		username = (draggable.textContent.substring(0, length-1));
	  content.textContent = username;
	}
  vesselOwners[index] = username;
  activeusers.push(username);
	
	//try { if(!content.innerText) content.innerText = content.textContent; } catch(e) {}
	var link = document.createElement("a");
	Element.extend(link);
	
	link.addClassName("close");
	link.textContent = "X";
	//link.onclick = removeelement;	
	link.onclick = function () { removeelement(link); };
	
	try { if(!link.innerText) link.innerText = link.textContent; } catch(e) {}
	content.appendChild(link);
	newlyAdded.appendChild(content);
	droppable.appendChild(newlyAdded);
	newlyAdded.addClassName("removable");
	validate();
}

function createAddUserBox(lastheight) {
	var user = document.createElement("li");
	Element.extend(user);
	
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

  var username;
  var length;
	if (supportsInnerText()) {
    length = draggable.innerText.length;
    username = (draggable.innerText.substring(0, length-1));
  } else {
	  length = draggable.textContent.length;
    username = (draggable.textContent.substring(0, length-1));
  }
  
	var index = (Number)(droppable.id.charAt(8));
	
	if (vesselUsers[index].indexOf(username) != -1) {
    alert("That username already exists in this vessel!");
    return;
  }
	
	var lastheight = parseInt(droppable.lastChild.style.height);
	droppable.lastChild.remove();
	var newlyAdded = document.createElement("li");
	Element.extend(newlyAdded);
	
	if ($("user" + index + "-1")) { 
		var lastchildID = droppable.lastChild.id
		newlyAdded.id = "user" + index + "-" + ((Number)(lastchildID.substring(6, lastchildID.length)) + 1);
	} else {
		newlyAdded.id = "user" + index + "-1";
	}
	var link = document.createElement("a");
	Element.extend(link);
	
	link.addClassName("close");
	link.textContent = "X";
	//link.onclick = removeelement;
	link.onclick = function () { removeelement(link); };
	
	try { if(!link.innerText) link.innerText = link.textContent; } catch(e) {}
	var content = document.createElement("p");
	Element.extend(content);
	
	content.addClassName("container");
	
	//var length = draggable.textContent.length;
	//content.textContent = (draggable.textContent.substring(0, length-1));
	if (supportsInnerText()) {
    //var length = draggable.innerText.length;
    content.innerText = (draggable.innerText.substring(0, length-1));
  } else { 
	  //var length = draggable.textContent.length;
	  content.textContent = (draggable.textContent.substring(0, length-1));
	}
	
	
	//try { if(!content.innerText) content.innerText = content.textContent; } catch(e) {}
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
	//alert(droppable.childNodes[0]);
	
	if (supportsInnerText()) {
	  vesselUsers[index][userTally[index]] = (draggable.innerText.substring(0, length-1));
	} else {
    vesselUsers[index][userTally[index]] = (draggable.textContent.substring(0, length-1));
  }
	
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

function pre_addUser () {
  $("add").disabled = true;
	$("add").value = "Wait...";
}


/* add users to the user box */
function addUser () {
	if ($("username").value == "") {
		$("username").value = "user_" + counter;
	}
	var name = $("username").value;
	
	if (name == "user_" + counter) {
		counter++;
	}
	
	//if (users.indexOf(name) == -1) {
  //users.push(name);
		var user = document.createElement("span");
		Element.extend(user);
		
		var close = document.createElement("a");
		Element.extend(close);
		
		user.addClassName("user");
		user.id = name;
		
		//user.textContent = name;
		changeTextById(user, name);
		
		//close.textContent = "x";
		changeTextById(close, "x");
		
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
	//}
	
	resetForm();
	
	/*
	new Ajax.Request('/html/add_user',
		{
			method: "post",
			parameters: {action: "resetform", username: name},
			onSuccess: resetForm
		}
	);
	*/

}

/*  guess the username for given public key  */
function updateUsername () {
	if ($("publickey").value != "") {
		$("username").value = $("publickey").value.substring($("publickey").value.lastIndexOf("/") +1,
															 $("publickey").value.lastIndexOf("."));
	}
}

/*  automatically increment the username by one  */
function resetForm () {
  if ($("publickey").value == "") {
    $("username").value = "user_" + counter;
  } else {
    $("username").value = "";
  }
  $("publickey").value = "";

	$("add").disabled = false;
  $("add").value = "Add User";
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
	new Ajax.Request('/html/create_installer',
		{
			method: "post",
			parameters: {action: "createinstaller", content: jsonString},
			onSuccess: finish,
			onFailure: createinstaller_error
		}
	);
}

/*  redirect the page to installer download page  */
function finish (ajax) {
	location.href = "/html/download_keys";
}

function createinstaller_error (ajax) {
  document.write(ajax.responseText)
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

// Changes text using the correct browser-specific method
function changeTextById(element, changeVal) {
  var hasInnerText = (document.getElementsByTagName("body")[0].innerText != undefined) ? true : false;
  
  if(!hasInnerText){
    element.textContent = changeVal;
  } else {
    element.innerText = changeVal;
  }
}

function supportsInnerText() {
  return (document.getElementsByTagName("body")[0].innerText != undefined) ? true : false;
}