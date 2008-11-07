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
	$("banner").style.minWidth = "700px";
	if (BrowserDetect.browser == "Explorer") {
		var spacers = $$(".spacer");
		spacers[0].style.height = "30px";
		//$$(".mainwindow")[0].paddingBottom = "10%";
		$("window3").style.minWidth = "740px";
		$("banner").style.minWidth = "735px";
		$("welcome").style.minWidth = "695px";
		$("header").style.marginBottom = "0px";
		$("header").style.paddingLeft = "0px";
		$("header").style.width = "98%";
		alert(BrowserDetect.version);
		alert("test2");
	} else {
		$("welcome").style.minWidth = "600px";
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
	if ($("table1")) {
		$("table1").style.display = "block";
	}
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
	if ($("table2")) {
		$("table2").style.display = "block";
	}
	var maximizer2 = $("maximizer2");
	$("maximizer2").textContent = count2 + " Machines (click to hide)";
	try { if(!maximizer2.innerText) maximizer2.innerText = maximizer2.textContent; } catch(e) {}
	$("maximizer2").onclick = table2hide;
}

function tally() {
	var list1 = $$(".table1row");
	var list2 = $$(".table2row");
	var list3 = $$(".table3row");
	count1 = list1.length;	
	count2 = list2.length;
	count3 = list3.length;
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

