/***************************************************************************
<File Name>
 resourcemanager.js

<Started>
  November 25, 2008

<Author>
  plipay@u.washington.edu
  Peter Lipay

<Purpose>
  Constantly refreshes the tables and graphical displays on the resourcemanager.html page 
  using data from a file named "status" present in the same directory as this javascript.
  It is assumed that the "status" file carries the following format of comma seperated values:
  First is the Name of the Vessel Owner (Jim, Frank, whatever),
  Second is a Decimal value representing the allocated percentage for that vessel out of 100% ,
  Third is a Decimal value representing the in use percentage for that vessel out of 100%,
  Another important point is there must be exactly one empty line at the end of the data file    
  For Example:
Jane , 30.0 , 11.0
Justin , 50.0 , 75.2
Issac , 20.0 , 14.3
(empty line)
***************************************************************************/

var REFRESHRATEINSECONDS = 5; //This specifies the refresh rate of the page in seconds (how often it reupdates the values on the page)
var g_totalallocatedunderfive = 0; //This keeps track of the number of vessels which have under 5% allocated and is used to build the "<5%" block
var g_totalusageunderfive = 0; //This keeps track of the total % in use by the vessels which have less than 5% allocated and is used to build the "<5%" block
 /*The below variable is used mainly for an IE6 problem, where the browser would make multiple AJAX calls to the data file almost simultaneously, instead of once per the refresh rate. 
I corrected this using a simple true/false switch that ensures that the update method is only called once per refresh rate, and the below variable stores the current state (true or false).
*/
 var g_justupdated = false;								
/*The array below stores the background color of each of the vessels (the td elements). Since the floating Vessel Labels ("V1, V2, etc)  are implemented using a background image stored in the same 
directory, if you wish to change these without screwing up the look of the page, you will also need to change the background color in each of the corresponding image files . 
Right now the colors alternate between three slightly different shades, they're close enough that the semi-transparent green progress bars (the "fill" divs) are about the same shade of green, but different 
enough to be distinguishable to the user
*/
var g_vesselcolors = ["#FFFFCC", "#fffee6", "#fdfdfd", "#FFFFCC", "#fffee6", "#fdfdfd", "#FFFFCC", "#fffee6", "#fdfdfd", "#FFFFCC", "#fffee6", "#fdfdfd", "#FFFFCC", "#fffee6", "#fdfdfd", "#FFFFCC", "#fffee6", "#fdfdfd", "#FFFFCC", "#fffee6", "#fdfdfd"];

//Onload, the page is refreshed once, and then sets up a timer which refreshes the page every 'refreshrateinseconds' seconds
window.onload = function() {
	call(); 
	setInterval(call, REFRESHRATEINSECONDS * 1000);	
};

//This function makes an ajax call to a file in the same directory as this javascript, called "status" (which stores the data used by this webpage).
//Once the info is returned, the update method is called with this data.
function call() {
	g_justupdated = false;
	/*Since Internet Explorer doesn't support Ajax.Request objects to be used on calls to local directories, this manual approach is necessary*/
	if (navigator.userAgent.match(/.*(MSIE 7.0)|(MSIE 6.0)/)) {
		xmlhttp = getXmlHttp();
		xmlhttp.open("GET", "status", true);
		xmlhttp.onreadystatechange = function() {
			update(xmlhttp);
		}
		xmlhttp.send(null);
		
	}
	new Ajax.Request("status", 
	{
		method: "get",
		onSuccess: update,
		onFailure: error
	});

}

/* This function returns an xml object if the browser supports it or alerts an error message if the object isn't supported*/
function getXmlHttp() {
	xmlhttp=new ActiveXObject("Microsoft.XMLHTTP");
	if (xmlhttp == null) {
		alert("Your Browser Doesn't Support XMLHTTP");
	}
	return xmlhttp;
}

/*This function handles all of the updating for the page, including refreshing of table data, and refreshing of the graphical representations 
   of the vessels. More detailed explanations are written for each section.
*/
function update(Ajax) {
	if (!g_justupdated) {
		/*This loop rezeroes the vessel data in the graphical representation, to make the refreshing work properly (without this the graphical vessel list will grow in size during every refresh)*/
		for (var z = 1;z < 21;z++) {
			$("row" + z).style.display = "none";
			$("row" + z).style.height = "0px";
			$("row" + z).parentNode.style.display = "none";
			$("row" + z).parentNode.style.height = "0px";
			
		}
		/*The following variable and loop rezero the data tables, to make refreshing work properly (again, the tables will grow in size during every refresh without this).*/
		var table2elementstoremove = $$(".addedtotable2");
		for (var j=0;j<table2elementstoremove.length;j++) {
			table2elementstoremove[j].remove();
		}
		/*Finally, this statement rezeroes the <5% graphical block so that it doesn't grow on every refresh*/
		$("row21").style.display = "none";
		$("row21").parentNode.style.display = "none";
		
		//The 'vessels' variable  stores an array of vessels, with each array element having a line of data about that particular vessel
		if (navigator.userAgent.match(/.*(MSIE 7.0)|(MSIE 6.0)/)) {
			var vessels = Ajax.responsetext.split("\n");
		} else {
			var vessels = Ajax.responseText.split("\n");
		}
		
		/*This will sort the vessels in order of greatest allocated to smallest allocated. This is necessary because of the way the floating Text headers (V1, V2, etc)
		    Since the headers are implemented using images (of which there are only 20), we run into the problem that if you have a bunch of less than 5% vessels (say, 30) first,
		    then when we have a greater than 5% vessel (say Vessel #31), we don't have a V31 image. To address this, the vessels must be sorted from greatest to lowest. We do 
	               this using the Array objects build in sort method, and we pass it a custom function 'compare' that sets up rules for comparing the vessels.
		*/
		vessels.sort(compare);
		
		
		/*This loop handles the detailed elements of refreshing the page, cycling through each of the vessels present in the "vessels" variable.
		It first rebuilds the data tables, then, if the current vessel has less than 5% allocated it increments the global variables totalallocatedunderfive 
		and totalusageunderfive (to be later used in the < 5% graphical block). Otherwise, if the current vessel has at least 5% allocated, the loop 
		displays the current vessel on the page with the correct height and usage .
		*/
		for (var i=1;i<=vessels.length-1;i++) {
			/* The below variable 'vesselinfo' is an array that stores the data for the current vessel being processed. So, vesselinfo[0] will give the vessel name (V1, V2, etc),
			vesselinfo[1] will give the vessel owners name, vesselinfo[2] will give the vessels allocated percentage, and vesselinfo[3] will give the percentage currently in use by this vessel*/
			var vesselinfo = vessels[i-1].split(","); 		
			/*The next section populates the data tables by creating and appending new rows and columns*/
			
			/*Here we create our row and column elements*/
			var newinforow = document.createElement("tr");
			newinforow.className = "addedtotable2"; //This is done so that it is easy to remove this same element on the next refresh
			var newinfocolumn1 = document.createElement("td");
			var newinfocolumn2 = document.createElement("td");
			var newinfocolumn3 = document.createElement("td");
			var newinfocolumn4 = document.createElement("td");
			
			/*Here we populate our column elements*/
			newinfocolumn1.textContent = "V" + i;
			newinfocolumn2.textContent = vesselinfo[0];
			newinfocolumn3.textContent = vesselinfo[1] + "%";
			newinfocolumn4.textContent = vesselinfo[2] + "%";
			/* The following try statements are done as a workaround for IE, as IE doesn't support the above textContent property*/
			try { if(!newinfocolumn1.innerText) newinfocolumn1.innerText = newinfocolumn1.textContent; } catch(e) {}
			try { if(!newinfocolumn2.innerText) newinfocolumn2.innerText = newinfocolumn2.textContent; } catch(e) {}
			try { if(!newinfocolumn3.innerText) newinfocolumn3.innerText = newinfocolumn3.textContent; } catch(e) {}
			try { if(!newinfocolumn4.innerText) newinfocolumn4.innerText = newinfocolumn4.textContent; } catch(e) {}
			
			/*Here we append our new columns to our new row and append our new row to the table*/
			newinforow.appendChild(newinfocolumn1);
			newinforow.appendChild(newinfocolumn2);
			newinforow.appendChild(newinfocolumn3);
			newinforow.appendChild(newinfocolumn4);
			$("keybody").appendChild(newinforow);
			
			/*This if block handles the case of a vessel having less than 5% allocated to it, thus, populating the special table of vessels
			with less than 5% , and tallying the global variables so that the <5% resources vessel block will come into existence later on in the code*/
			if (vesselinfo[1] < 5.0) {
				g_totalallocatedunderfive += parseFloat(vesselinfo[1]); //This tallies the total amount allocated to the <5% block
				/*This tallies the total amount in use by the <5% block . Since its assumed that the usage percentage provided in the data file is
				in terms of the percent allocated the below calculation is necessary. For instance, if in the data file 100% is listed as the usage percentage,
				this is assumed to mean 100% of that particular vessel, so if that vessel only has 2% allocated to it, then only 2% is being used, not 100%.
				The below calculation makes this conversion happen.
				*/
				g_totalusageunderfive += ((vesselinfo[2]/100)*vesselinfo[1]); 
				
				/*This section updates the <5% table which lists the vessels that make up the <5% block*/
				
				/*First we create the row and column elements*/
				var newrow = document.createElement("tr");
				newrow.className = "addedtotable2"; //Again, this makes this row easier to delete on the next update
				var newcolumn1 = document.createElement("td");
				var newcolumn2 = document.createElement("td");
				var newcolumn3 = document.createElement("td");
				
				/*Then we populate the column elements*/
				newcolumn1.textContent = "V" + i;
				newcolumn2.textContent = vesselinfo[1] + "%";
				newcolumn3.textContent = vesselinfo[2] + "%";
				/*This is the IE fix for textContent mentioned earlier*/
				try { if(!newcolumn1.innerText) newcolumn1.innerText = newcolumn1.textContent; } catch(e) {}
				try { if(!newcolumn2.innerText) newcolumn2.innerText = newcolumn2.textContent; } catch(e) {}
				try { if(!newcolumn3.innerText) newcolumn3.innerText = newcolumn3.textContent; } catch(e) {}
				
				/*Finally, we append the columns to the row and the row to the table*/
				newrow.appendChild(newcolumn1);
				newrow.appendChild(newcolumn2);
				newrow.appendChild(newcolumn3);
				$("toosmallbody").appendChild(newrow);
				
			/*Now, if the current vessel has at least 5% allocated to it, then it will show up on the page as its own vessel and not part of the <5% block, so we 
			display the vessel using the below conditional code block.
			*/
			} else {
				/*First we unhide the vessel and make it display on the page*/
				$("row" + i).style.display = "block";
				$("row" + i).parentNode.style.display = "block";
				
				/*Then we set its background color*/
				$("row" + i).style.backgroundColor = g_vesselcolors[i-1];
			
				/*We must set the height of the td element using pixels for it to work, so the below variable takes the percentage height from the data file 
				for the current vessel and converts it to pixels*/
				var currentHeight = Math.round(vesselinfo[1]*5);
				
				/*Now we set the proper allocated height of the current td element */
				$("row" + i).style.height = currentHeight + "px";
				$("row" + i).parentNode.style.height = currentHeight + "px";
				
				/*Now we set the proper height for the green progress bar inside our current td element. As mentioned before, the calculation below converts the relative percentage in 
				the data to an absolute percentage for the whole graph, and then converts the height to pixels. This is necessary for the green bar to display properly in all browsers.*/
				$("fill" + i).style.height = ((vesselinfo[2]*.01 * vesselinfo[1])*5) + "px";
				
				/*Here we set a background image for the td element to take care of the floating text Caption on each of the vessels (V1, V2, V3). This was the only clean way I could come up
				with to get the text to float perfectly in the center above the green TD element. The only alternative I've found is to use absolute or relative positioning, which becomes a 
				nightmare quickly. So while this does add the burden of several images to load on the page, I think its worth it for code simplicity and cleanlines*/
				$("row" + i).style.backgroundImage = "url(\"V" + i + ".jpg\")";
				/*These are just a few IE specific fixes.*/  
				if (navigator.userAgent.match(/.*(MSIE 7.0)|(MSIE 6.0)/)) {
					/*The below two statements make sure that the empty and fill divs are being displayed*/
					$("empty" + i).style.display = "block"; 
					$("fill" + i).style.display = "block";
					/*This statement causes a second div inside the td element to fill up any remaining space inside the td. This is necessary so that
					the green bar doesn't float in the middle of the td element in IE browsers. */
					$("empty" + i).style.height = (100 - (vesselinfo[2])) + "%";
					/*The below two if statements help address some bizare IE6 visual bugs */
					if ((100 - (vesselinfo[2])) <= 2) {
						$("empty" + i).style.display = "none";					
					}
					if (vesselinfo[2] == 0) {
						$("fill" + i).style.display = "none";
					}
					/*This statement is done because IE prefers the height to be assigned in percentages while 
					firefox seems to prefer it in pixels*/
					$("fill" + i).style.height = vesselinfo[2] + "%";
					/*This statement takes care of some minor visual glitches in IE*/
					$("fill" + i).style.borderBottom = "1px solid " + g_vesselcolors[i-1];
				}
			}
		}
		/*Lastly, this conditional creates the <5% graphical block is any of the vessels were less than 5%*/
		if (g_totalallocatedunderfive > 0) {
			/*So, we first unhide the block and make it display on the page*/
			$("row21").style.display = "block";
			$("row21").parentNode.style.display = "block";
			
			/*Then we set its background color*/
			$("row21").style.backgroundColor = g_vesselcolors[20];
		    
			/*Now we set its height, done in pixels for Firefox's sake*/
			$("row21").style.height = g_totalallocatedunderfive*5 + "px";
			$("row21").parentNode.style.height = g_totalallocatedunderfive*5 + "px";
			
			/*Now we set the proper height for the green bar, again changing from a relative to an absolute percent so that it's displayed properly (100% of 2% allocated should still be 2% of the table height)*/
			$("fill21").style.height = ((g_totalusageunderfive/g_totalallocatedunderfive)*100) + "%";
			
			/*Now we set the background image to take care of the floating < 5%*/
			$("row21").style.backgroundImage = "url(\"V21.jpg\")";
			
			/*And again, a few specific IE fixes*/
			if (navigator.userAgent.match(/.*(MSIE 7.0)|(MSIE 6.0)/)) {
				/* Our <5% block can never be less than the font size of our "< 5%" caption. It is true that this creates some slightly eronous graphical displays when a really tiny amount is allocated, but its important
				that the page never look broken, and past a certain point it doesn't make sense to keep shrinking the block. Since we always have the raw data displayed in the tables for the user anyway, I think its an 
				easy compromise to make. While we can take care of this with a simple "min-height" statement in the CSS, IE doesn't support min-height, requiring the workaround in the conditional below.
				*/
				if (parseInt($("row21").style.height) < 15) {
					$("row21").style.height = "15px";
					$("row21").parentNode.style.height = "15px";	
				}
				/*And again, as mentioned earlier, this fills up the remaining space in the td element of that the green progress bar doesn't float in the middle of the table in IE.*/
				$("empty21").style.height = 100 - ((g_totalusageunderfive/g_totalallocatedunderfive)*100) + "%";
			}
		}
		/*The following statements rezero the global variables */
		g_totalusageunderfive = 0;
		g_totalallocatedunderfive = 0;
		//g_coloroffset = 0;
		g_justupdated = true;
	}
}

//Prints an error message if the ajax call fails
function error() {
	alert("Error, Ajax call failed");
}

/*This function is comparing two vessel array elements (a and b).
It returns -1 if the allocated amount of vessel a is greater than the allocated amount of vessel b.
It returns 1 if the allocated amount of vessel b is greater than the allocated amount of vessel a.
It returns 0 if the allocated amount of vessel a and vessel b is equal
*/
function compare(a, b) {
	var currenta = a.split(",");
	var currentb = b.split(",");
	if (parseFloat(currenta[1]) > parseFloat(currentb[1])) {
		return -1;
	} else if (parseFloat(currenta[1]) < parseFloat(currentb[1])) {
		return 1;
	} else {
		return 0;
	}
}