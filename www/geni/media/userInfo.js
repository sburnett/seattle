window.onload = function() {
	$("welcome").style.minWidth = "300px";
	$("banner").style.minWidth = "450px";
	$("header").style.minWidth = "350px";
	if (BrowserDetect.browser == "Explorer") {
		$("header").style.marginBottom = "0px";
		$("banner").style.minWidth = "450px";
		$("welcome").style.minWidth = "340px";
		$("header").style.marginBottom = "0px";
		$("header").style.paddingLeft = "10px";
		$("header").style.width = "98%";
	}
	if (BrowserDetect.browser == "Konqueror") {
		$$("body")[0].style.fontSize = "10pt";
		$$(".compressed-side-window")[0].style.fontSize = "10pt";
		$$(".donation_table")[0].style.fontSize = "8pt";
	}
}

/*Function used by the CSS to make a hack workaround for min-width that works properly in IE*/
function RemoveUnits(txt) {
	var temp = txt.replace(/px|cm|pt|em|en|auto/,'');
	return isNaN(temp) ? 0 : parseInt( temp );
}

/*Function used by the CSS to make a hack workaround for min-width that works properly in IE*/
function IE6MinWidth( el, size ){
	var max = (this.IE6MaxWidth ? this.IE6MaxWidth : this.IE6MaxWidth = RemoveUnits(el.currentStyle.paddingLeft) + RemoveUnits(el.currentStyle.marginLeft) + RemoveUnits(el.currentStyle.borderLeftWidth) + size + 1);
	if (document.documentElement.clientWidth > max) {
		return "auto";
	} else {
		return size+"px";
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
