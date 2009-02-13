$(document).ready(function() {
	load();
	/*
	var credits = $("#credits");
	var creditnames = $("#creditnames");
	create_block(credits, "Me", 35, false);
	create_block(credits, "Ivan", 25, false);
	create_block(credits, "Justin", 15, false);
	create_block(credits, "Sean", 10, false);
	create_block(credits, "Others", 15, false);
	
	create_label(creditnames, "Me", 35, false);
	create_label(creditnames, "Ivan", 25, false);
	create_label(creditnames, "Justin", 15, false);
	create_label(creditnames, "Sean", 10, false);
	create_label(creditnames, "Others", 15, false);
	
	var usage = $("#usage");
	var usagenames = $("#usagenames");
	create_block(usage, "Justin", 3, true);
	create_block(usage, "Kate", 5, true);
	create_block(usage, "Man", 8, true);
	create_block(usage, "Me", 21, true);
	create_block(usage, "Kevin", 14, true);
	create_block(usage, "Others", 14, true);
	create_block(usage, "Free", 35, true);
	create_label(usagenames, "Justin", 3, true);
	create_label(usagenames, "Kate", 5, true);
	create_label(usagenames, "Man", 8, true);
	create_label(usagenames, "Me", 21, true);
	create_label(usagenames, "Kevin", 14, true);
	create_label(usagenames, "Others", 14, true);
	create_label(usagenames, "Free", 35, true);
	*/
	
//	$("#getresourcesbutton").click(get_resources_dialog);
	$("#getresourcesdialog button").click(close_dialog);
	
//	$("#shareresources").click(share_resources_dialog);
	$("#shareresourcesdialog button").click(close_dialog);
	

});

/*

function add_user(username, width, isClosable) {
	var credits = $("#credits");
	var creditnames = $("#creditnames");
	create_block(credits, username, width, isClosable);
	create_label(creditnames, username, width, isClosable);
}
*/

/*
	Create a block with given width and background color,
	and append it to the given bar element.
*/
function create_block(bar, username, width, isClosable) {
	var block = $(document.createElement('td'));
	block.css({
		'width': width + '%',
		'background-color': '#' + color_generator(username)
	});
	var percent = $(document.createElement('span'));
	percent.text(width + '%');

	if (isClosable) {
		block.attr("id", "usage" + username);
		if (username == "Free") {
			var get = $(document.createElement('a'));
			get.attr('id','getresourcesbutton');
			get.attr('href','#');
			get.text('get');
			get.click(get_resources_dialog);
			block.append(get);
			
			var share = $(document.createElement('a'));
			share.attr('id','shareresources');
			share.attr('href','#');
			share.text('share');
			share.click(share_resources_dialog);
			block.append(share);
			
		} else if (username != "Me" && username != "Others" ) {
			var close = $(document.createElement('a'));
			close.attr('href','#');
			close.text('x');
			close.click(function() {
				edit_block(username, 0);
			});
			block.append(close);
			percent.click(change_percent);
		}
	}
	
	if (username == "Others") {
		percent.click(function () { show_table(isClosable) });
	}
	
	block.append(percent);
	bar.append(block);
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


/*
	Create a name label with given width and append it to
	the given name table.
*/
function create_label(names, username, width, isClosable) {
	var label = $(document.createElement('td'));
	if (isClosable) {
		label.attr("id", "labelusage" + username);
	}
	label.text(username);
	label.css({
		'width': width + '%'
	});
	names.append(label);
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
	$.post("http://128.208.3.86:8081/geni_dev_sean/control/ajax_editshare",
			{ username: username, percent: width },
			function (data) {
				var json = eval(data);
				if (json.success) {
					$(this).parent().remove();
					$("#dialogframe").hide();
					$("#overlay").hide();
					edit_block(username, percent);
				} else {
					$(this).prev().prev().remove();
					$(this).prev().prev().remove();
					var warning = $(document.createElement("span"));
					warning.text(json.error);
					warning.addClass("warning");
					warning.insertBefore($(this).prev().prev());
				}
	   		},
			"json");
}


/*
	Toggle display the tables for small percent users
*/
function show_table(isClosable) {
	if (isClosable) {
		$("#usageothers").toggle();
	} else {
		$("#creditothers").toggle();
	}
}



function get_resources_dialog() {
	$("#dialogframe").fadeIn("fast");
	$("#overlay").fadeIn("fast");
	$("#getresourcesdialog").fadeIn("fast");
}


function share_resources_dialog() {
	$("#dialogframe").fadeIn("fast");
	$("#overlay").fadeIn("fast");
	$("#shareresourcesdialog").fadeIn("fast");
}

function close_dialog() {
	$(this).parent().parent().hide();
	$("#dialogframe").hide();
	$("#overlay").hide();
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
	$.post("http://128.208.3.86:8081/geni_dev_sean/control/ajax_getcredits",
		function (data) { update_blocks("credits", data); }, 
		"json");
	$.post("http://128.208.3.86:8081/geni_dev_sean/control/ajax_getshares",
		function (data) { update_blocks("shares", data); }, 
		"json");
}


function update_blocks(type, data) {
	if (type == "credits") {
		var credits = $("#credits");
		var creditnames = $("#creditnames");
		json = eval('(' + data + ')');
		for (var i = 0; i < json.length; i++) {
				create_block(credits, json[i].username, json[i].percent, false);
			create_label(creditnames, json[i].username, json[i].percent, false);
		}
	} else if (type == "shares") {
		var usage = $("#usage");
		var usagenames = $("#usagenames");
		json = eval('(' + data + ')');
		var total_percent = 0;
		for (var i = 0; i < json.length; i++) {
			create_block(usage, json[i].username, json[i].percent, true);
			create_label(usagenames, json[i].username, json[i].percent, true);
			total_percent += json[i].percent;
		}
		create_block(usage, "Free", 100 - total_percent, true);
		create_label(usagenames, "Free", 100 - total_percent, true);
	}
}
