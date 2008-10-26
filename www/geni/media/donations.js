var count1 = 0;
var count2 = 0;
var count3 = 0;
var hideWhenNumber = 8;
var dontDisplay = 3;

window.onload = function() {
	if (BrowserDetect.OS == "Windows") {
		$("win").src = "/geni/media/midwin.jpg";
	} else if (BrowserDetect.OS == "Mac") {
		$("osx").src = "/geni/media/midosx.jpg";
	} else if (BrowserDetect.OS == "Linux") {
		$("linux").src = "/geni/media/midlinux.jpg";
	} else {
	}
	if (BrowserDetect.browser == "Explorer") {
		var notices = $$(".notices");
		for (var i = 0;i < notices.length;i++) {
			notices[i].style.position = "absolute";
			notices[i].style.width = "50%";
			notices[i].style.left = "25%";
			notices[i].style.right = "25%";
		}
		var parent = $("installerLink").parentNode;
		$("installerLink").remove();
		element = $("installerLink2");
		element.textContent = "Installers Page";
		try { if(!element.innerText) element.innerText = element.textContent; } catch(e) {}
		element.id = "installerLink";
		element.position = "absolute";
		element.style.left = "10%";
		element.style.fontSize = "18pt";
		element.style.border = "1px solid black";	
	} else {
		$("installerLink").style.height = "50px";
	}
	//$("checkAll").onclick = checkAll;
	var count = tally();
	$("maximizer1").textContent = count1 + " Machines Donated (click to expand)";
	$("maximizer2").textContent = count2 + " Machines Donated (click to expand)";
	$("maximizer3").textContent = count3 + " Shares (click to expand)";
	try { if(!maximizer3.innerText) maximizer3.innerText = maximizer3.textContent; } catch(e) {}
	try { if(!maximizer1.innerText) maximizer1.innerText = maximizer1.textContent; } catch(e) {}
	try { if(!maximizer2.innerText) maximizer2.innerText = maximizer2.textContent; } catch(e) {}
	if (count1 >= hideWhenNumber) {
		$("maximizer1").onclick = table1unhide;
	} else if (count1 <= dontDisplay) {
		table1unhide();
		$("maximizer1").style.display = "none";
	} else {
		$("maximizer1").style.display = "block";
		table1unhide();
	}
	if (count2 >= hideWhenNumber) {
		$("maximizer2").onclick = table2unhide;
	} else if (count2 <= dontDisplay) {
		table2unhide();
		$("maximizer2").style.display = "none";
	} else {
		$("maximizer2").style.display = "block";
		table2unhide();
	}
	if (count3 >= hideWhenNumber) {
		$("maximizer3").onclick = table3unhide;
	} else if (count3 <= dontDisplay) {
		table3unhide();
		$("maximizer3").style.display = "none";
	} else {
		$("maximizer3").style.display = "block";
		table3unhide();
	}
};

function table3unhide() {
	$("sharedResources").style.display = "block";
	var maximizer3 = $("maximizer3");
	$("maximizer3").textContent = count3 + " Shares (click to hide)";
	try { if(!maximizer3.innerText) maximizer3.innerText = maximizer3.textContent; } catch(e) {}
	$("maximizer3").onclick = table3hide;
}

function table3hide() {
	$("sharedResources").style.display = "none";
	var maximizer3 = $("maximizer3");
	$("maximizer3").textContent = count3 + " Shares (click to expand)";
	try { if(!maximizer3.innerText) maximizer3.innerText = maximizer3.textContent; } catch(e) {}
	$("maximizer3").onclick = table3unhide;
}

function table1unhide() {
	$("table1").style.display = "block";
	var maximizer1 = $("maximizer1");
	$("maximizer1").textContent = count1 + " Machines (click to hide)";
	try { if(!maximizer1.innerText) maximizer1.innerText = maximizer1.textContent; } catch(e) {}
	$("maximizer1").onclick = table1hide;
}

function table1hide() {
	$("table1").style.display = "none";
	var maximizer1 = $("maximizer1");
	$("maximizer1").textContent = count1 + " Machines (click to expand)";
	try { if(!maximizer1.innerText) maximizer1.innerText = maximizer1.textContent; } catch(e) {}
	$("maximizer1").onclick = table1unhide;
}

function table2hide() {
	$("table2").style.display = "none";
	var maximizer2 = $("maximizer2");
	$("maximizer2").textContent = count2 + " Machines (click to expand)";
	try { if(!maximizer2.innerText) maximizer2.innerText = maximizer2.textContent; } catch(e) {}
	$("maximizer2").onclick = table2unhide;
}

function table2unhide() {
	$("table2").style.display = "block";
	var maximizer2 = $("maximizer2");
	$("maximizer2").textContent = count2 + " Machines (click to hide)";
	try { if(!maximizer2.innerText) maximizer2.innerText = maximizer2.textContent; } catch(e) {}
	$("maximizer2").onclick = table2hide;
}

function tally() {
	var list1 = $$(".table1row");
	var list2 = $$(".table2row");
	var list3 = $$(".table3row");
	for (var i = 0;i < list1.length;i++) {
		count1++;
	}
	for (var j = 0;j < list2.length;j++) {
		count2++;
	}
	for (var i = 0;i < list3.length;i++) {
		count3++;
	}
}

function checkAll() {
	var checkboxes = $$("check");
	for (var i = 0;i < checkboxes.length;i++) {
		checkboxes[i].checked = "true";
	}
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

