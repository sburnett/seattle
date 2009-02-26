var minwidth = 10;

$(document).ready(function() {
	load();
});

/*
	A cell is a combination of block and label
	Take care of cell order and cell minwidth
*/
function add_cell(type, username, percent) {
	if (type == "credits") {
		if (percent >= minwidth) {
			var block = create_block(username, percent, false);
			var label = create_label(username, percent, false);
			$("#credits").append(block);
			$("#creditnames").append(label);
		} else {
			var item = create_other(username, percent, false);
			$("#creditotherstable").append(item);
			if ($("#creditOthers").length > 0) {
				edit_cell(type, "Others", get_percent("credits", "Others") + percent);
			} else {
				var others = create_block("Others", get_percent("credits", "Others") + percent, true);
				var labelothers = create_label("Others", get_percent("credits", "Others") + percent, true);
				$("#credits").append(others);
				$("#creditnames").append(labelothers);
			}
		}
	} else if (type == "shares") {
		var block = create_block(username, percent, true);
		var label = create_label(username, percent, true);	
		
		if (username == "Free") {
			$("#usage").append(block);
			$("#usagenames").append(label);
		} else if (username == "Me") {
			if ($("#usageFree").length > 0) {
				block.insertBefore("#usageFree");
				label.insertBefore("#labelusageFree");
			} else {
				$("#usage").append(block);
				$("#usagenames").append(label);
			}
		} else if (percent >= minwidth) {
			if ($("#usageOthers").length > 0) {
				block.insertBefore("#usageOthers");
				label.insertBefore("#labelusageOthers");
			} else if ($("#usageMe").length > 0) {
				block.insertBefore("#usageMe");
				label.insertBefore("#labelusageMe");
			} else if ($("#usageFree").length > 0) {
				block.insertBefore("#usageFree");
				label.insertBefore("#labelusageFree");
			} else {
				$("#usage").append(block);
				$("#usagenames").append(label);
			}
		} else {
			var item  = create_other(username, percent, true);
			$("#usageotherstable").append(item);
			if ($("#usageOthers").length > 0) {
				edit_cell(type, "Others", get_percent("shares", "Others") + percent);
			} else {
				var others = create_block("Others", get_percent("shares", "Others") + percent, true);
				var labelothers = create_label("Others", get_percent("shares", "Others") + percent, true);
				if ($("#usageMe").length > 0) {
					others.insertBefore("#usageMe");
					labelothers.insertBefore("#labelusageMe");
				} else if ($("#usageFree").length > 0) {
					others.insertBefore("#usageFree");
					labelothers.insertBefore("#labelusageFree");
				} else {
					$("#usage").append(others);
					$("#usagenames").append(labelothers);
				}
			}
		}
	}
}


/*
	Return the percent of the given user in given bar type
*/
function get_percent(type, username) {
	var percent = 0;
	if (type == "credits") {
	 	percent = parseInt($("#credit" + username).css("width"));
	} else if (type == "shares") {
		percent = parseInt($("#usage" + username).css("width"));
	}
	return percent;
}


/*
	Create a block with given width and background color,
	and append it to the given bar element.
*/
function create_block(username, width, isShare) {
	var block = $(document.createElement('td'));
	block.css({
		'width': width + '%',
		'background-color': '#' + color_generator(username)
	});
	var percent = $(document.createElement('span'));
	percent.text(width + '%');

	if (isShare) {
		block.attr("id", "usage" + username);
		if (username == "Free") {
			var get = $(document.createElement('a'));
			get.attr('id','getresourcesbutton');
			get.attr('href','#');
			get.text('get');
			get.click(get_resources_dialog);
			block.append(get);
			
			var share = $(document.createElement('a'));
			share.attr('id','shareresourcesbutton');
			share.attr('href','#');
			share.text('share');
			share.click(share_resources_dialog);
			block.append(share);
			
		} else if (username != "Me" && username != "Others" ) {
			var close = $(document.createElement('a'));
			close.attr('href','#');
			close.text('x');
			close.click(function() {
				$.post("../control/ajax_editshare",
						{ username: username, percent: 0 },
						function (data) {
							var json = eval('(' + data + ')');
							if (json.success) {
								edit_block(username, 0);
							} else {
								alert(json.error);
							}
						});
			});
			block.append(close);
			percent.click(change_percent);
		}
	}
	
	if (username == "Others") {
		percent.click(function () { show_table(isShare) });
		block.attr("id", "creditOthers");
	}
	block.append(percent);
	return block;
}



/*
	Create a name label with given width and append it to
	the given name table.
*/
function create_label(username, width, isShare) {
	var label = $(document.createElement('td'));
	if (isShare) {
		label.attr("id", "labelusage" + username);
	}
	label.text(username);
	label.css({
		'width': width + '%'
	});
	return label;
}


function create_other(username, percent, isShare) {
	var tr = $(document.createElement("tr"));
	tr.addClass("{% cycle 'odd' 'even' %}");
	tr.html("<td>" + username + "</td><td>" + percent + "</td><td><button>Edit</button> <button>Delete</button></td>");
	return tr;
}


/*
	Change the block's width both in terms of its label and
	actual width. Resize free block to	fit the width of the bar.
	Remove the block from the usage bar if width is 0
	Called by save_percent or close on the block
*/
function edit_block(username, width) {
	if (username != "Free") {
		var block = $("#usage" + username);
		var label = $("#labelusage" + username);
		var old_percent = parseInt($("#usage" + username + " span").text());
		var free_percent = parseInt($("#usageFree span").text());
		var new_free_percent = free_percent + old_percent - width;
		if (new_free_percent >= 0) {
			if (width == 0) {
				block.remove();
				label.remove();
			} else {
				$("#usage" + username + " span").text(width + '%');
				block.css("width", width + '%');
				label.css("width", width + '%');
			}
			$("#usageFree span").text(new_free_percent + '%');
			$("#usageFree").css("width", new_free_percent + '%');
			$("#labelusageFree").css("width", new_free_percent + '%');
		}
	}
}

function edit_cell(type, username, percent) {
	if (type == "shares") {
		edit_block(username, percent);
	} else {
		var block = $("#credits" + username);
		var label = $("#creditnames" + username);
		if (percent == 0) {
			block.remove();
			label.remove();
		} else {
			$("#credits" + username + " span").text(percent + '%');
			block.css("width", percent + '%');
			label.css("width", percent + '%');
		}
	}
}


/*
	Display the change percent dialog box
*/
function change_percent() {
	var dialog = $(document.createElement("div"));
	dialog.attr("id", "changepercentdialog");
	dialog.html('<h3>Change Percent</h3>');
	var input = $(document.createElement("input"));
	input.attr("name", $(this).parent().attr("id"));
	input.attr("type", "text");
	input.val(parseInt($(this).text()));
	input.click(function () { $(this).val("") });
	var symbol = $(document.createElement("span"));
	symbol.html(" %<br />");
	var cancel = $(document.createElement("button"));
	cancel.text("Cancel");
	var save = $(document.createElement("button"));
	save.text("Save");
	cancel.click(function () {
		close_dialog();
		$(this).parent().remove();
	});
	save.click(save_percent);
	dialog.append(input);
	dialog.append(symbol);
	dialog.append(cancel);
	dialog.append(save);
	$("#dialogframe").append(dialog);
	$("#dialogframe").fadeIn("fast");
	$("#overlay").fadeIn("fast");
	$("#changepercentdialog").fadeIn("fast");
}


/*
	Save the percent of the the block when click "save" on the
	change_percent dialog box
*/
function save_percent() {
	var input = $("#changepercentdialog input");
	var percent = input.val();
	var username = input.attr("name").substring(5);
	$.post("../control/ajax_editshare",
			{ username: username, percent: percent },
			function (data) {
				var json = eval(data);
				if (json.success) {
					$("#changepercentdialog").remove();
					$("#dialogframe").hide();
					$("#overlay").hide();
					edit_block(username, percent);
				} else {
					create_warning(json.error, $("#changepercentdialog h3"));
				}
	   		},
			"json");
}



/*
	Toggle display the tables for small percent users
*/
function show_table(isShare) {
	if (isShare) {
		$("#usageotherstable").toggle();
	} else {
		$("#creditotherstable").toggle();
	}
}


function get_resources_dialog() {
	$("#dialogframe").fadeIn("fast");
	$("#overlay").fadeIn("fast");
	$("#getresourcesdialog").fadeIn("fast");
	$(".cancel").click(close_dialog);
	$("#getresourcesaction").click(get_resources);
}


function share_resources_dialog() {
	$("#dialogframe").fadeIn("fast");
	$("#overlay").fadeIn("fast");
	$("#shareresourcesdialog").fadeIn("fast");
	$(".cancel").click(close_dialog);
	$("#shareresources").click(share_resources);
}

function close_dialog() {
    if ($(this).parent().children(".warning")) {
		$(this).parent().children(".warning").remove();
    }
	$(this).parent().hide();
	$("#dialogframe").hide();
	$("#overlay").hide();
}

/*
function received_ajax(data, fun) {
	if data html ...
	else
		fun(data)
	
}


function post_ajax(url, args, fun) {
	$.post(url,
		args,	
				function (data) {
					if data html ...
					else	
					fun(data)
	}
}
*/




function share_resources() {
	var username = $("#shareresourcesdialog #username").val();
	var percent = parseInt($("#shareresourcesdialog #percent").val());
	if ($("#shareresourcesdialog .warning")) {
	    $("#shareresourcesdialog .warning").remove();
	}
	if (percent > 0) {
		// post_ajax(url, args, function () {...})
		$.post("../control/ajax_createshare",
				{ username: username, percent: percent },
				function (data) {
					// func(data);
					var json = eval('(' + data + ')');
					if (json.success) {
						$("#shareresourcesdialog").hide();
						$("#dialogframe").hide();
						$("#overlay").hide();
						add_cell("share", username, percent);
						/*
						create_block($("#usage"), username, percent, true);
						create_label($("#usagenames"), username, percent, true);
						*/
					} else {
						create_warning(json.error, $("#shareresourcesdialog h3"));
					}
				});
	} else {
		create_warning("Percent must greater than 0", $("#shareresourcesdialog h3"));
	}
}


function get_resources() {
	var numvessels = parseInt($("#numvessels").val());
	var env = $("#environment").val();
	if ($("#getresourcesdialog .warning")) {
	    $("#getresourcesdialog .warning").remove();
	}
	$.post("../control/ajax_getvessels",
			{ numvessels: numvessels, env: env },
			function (data) {
				var json = eval('(' + data + ')');
				alert(json.mypercent);
				alert(json.success);
				if (json.success) {
					$("#getresourcesdialog").hide();
					$("#dialogframe").hide();
					$("#overlay").hide();
					add_cell("share", "Me", parseInt(json.mypercent));
					/*
					create_block($("#usage"), "Me", parseInt(json.mypercent), true);
					create_label($("#usagenames"), "Me", parseInt(json.mypercent), true);
					*/
				} else {
					create_warning(json.error, $("#getresourcesdialog h3"));
				}
			});
}



function create_warning(error, position) {
	var warning = $(document.createElement("p"));
	warning.html(error);
	warning.addClass("warning");
	warning.insertAfter(position);
}

/*
	Generate a color in hex notation for a username, which assigns different
	colors to different usernames.
*/

function color_generator(username) {
	var seeds = ['cc','ff'];
	var color = seeds[username.charCodeAt(0) % 2] +
				seeds[username.charCodeAt(1) % 2] +
				seeds[username.charCodeAt(username.length - 1) % 2];
	if (color == "ffffff") {
		color = "ffffcc";
	} else if (color == "cccccc") {
		color = "ccccff";
	}
	if (username == "Free") {
		color = "ffffff";
	} else if (username == "Me") {
		color = "cccccc";
	}
	return color;
}


function load() {
	$.post("../control/ajax_getcredits",
		function (data) { update_blocks("credits", data); }, 
		"json");
	$.post("../control/ajax_getshares",
		function (data) { update_blocks("shares", data); }, 
		"json");
}


function update_blocks(type, data) {
	var json = eval('(' + data + ')');
	var total_percent = 0;
	for (var i = 0; i < json.length; i++) {
		add_cell(type, json[i].username, json[i].percent);
		total_percent += json[i].percent;
	}
	if (type == "shares") {
		add_cell(type, "Free", 100 - total_percent);
	}
	
	/*
	if (type == "credits") {
		var credits = $("#credits");
		var creditnames = $("#creditnames");
		var json = eval('(' + data + ')');
		for (var i = 0; i < json.length; i++) {			
			create_block(credits, json[i].username, json[i].percent, false);
			create_label(creditnames, json[i].username, json[i].percent, false);
		}
	} else if (type == "shares") {
		var usage = $("#usage");
		var usagenames = $("#usagenames");
		var json = eval('(' + data + ')');
		var total_percent = 0;
		for (var i = 0; i < json.length; i++) {
			create_block(usage, json[i].username, json[i].percent, true);
			create_label(usagenames, json[i].username, json[i].percent, true);
			total_percent += json[i].percent;
		}
		create_block(usage, "Free", 100 - total_percent, true);
		create_label(usagenames, "Free", 100 - total_percent, true);
	}
	*/
}
