
$(document).ready(function() {
	update_credits();
	update_shares();
});



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
		if (username == "Free" && width > 0) {
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
								update_shares();
							} else {
								alert(json.error);
							}
						});
			});
			block.append(close);
			percent.attr("title", "Click to change percent");
			percent.tooltip({cssClass:"tooltip"});
			percent.css("cursor", "pointer");
			percent.click(function() {
				change_percent(username, width);
			});
		}
	}
	
	if (username == "Others") {
		percent.attr("title", "Click to reveal");
		percent.tooltip({cssClass:"tooltip"});
		percent.css("cursor", "pointer");
		percent.click(function () { show_table(isShare) });
		// block.attr("id", "creditOthers");
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


function add_other(type, username, percent) {
	var table;
	if (type == "credits") {
		table = $("#creditotherstable");
	} else if (type == "shares") {
		table = $("#usageotherstable");
	}
	var tr = $(document.createElement("tr"));
	tr.html("<td>" + username + "</td><td>" + percent + "</td>");
	if (type == "shares") {
		var control = $(document.createElement("td"));
		var edit = $(document.createElement("button"));
		edit.text("Edit");
		edit.click(function() {
			change_percent(username, percent);
		});
		var close = $(document.createElement("button"));
		close.text("Delete");
		close.click(function() {
			$.post("../control/ajax_editshare",
					{ username: username, percent: 0 },
					function(data) {
						var json = eval('(' + data + ')');
						if (json.success) {
							update_shares();
						} else {
							alert(json.error);
						}
					});
			tr.remove();
		});
		control.append(edit);
		control.append(close);
		tr.append(control);
	}
	table.append(tr);
}



/*
	Display the change percent dialog box
*/
function change_percent(username, percent) {
	var dialog = $(document.createElement("div"));
	dialog.attr("id", "changepercentdialog");
	dialog.html('<h3>Change Percent</h3>');
	var input = $(document.createElement("input"));
	input.attr("type", "text");
	input.val(percent);
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
	save.click(function() {
		 save_percent(username, parseInt(input.val()));
	});
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
function save_percent(username, percent) {
	$.post("../control/ajax_editshare",
			{ username: username, percent: percent },
			function (data) {
				var json = eval(data);
				if (json.success) {
					$("#changepercentdialog").remove();
					$("#dialogframe").hide();
					$("#overlay").hide();
					update_shares();
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


function post_ajax(url, args, func) {
	$.post(url, args, function(data) {
		// check data
		// if data ok then:
		func(data)
		// else:
		// display content as raw html in a new popup
	});
}


function share_resources() {
	var username = $("#shareresourcesdialog #username").val();
	var percent = parseInt($("#shareresourcesdialog #percent").val());
	if ($("#shareresourcesdialog .warning")) {
	    $("#shareresourcesdialog .warning").remove();
	}
	if (percent > 0) {
		post_ajax("../control/ajax_createshare",
				{ username: username, percent: percent },
				function(data) {
					var json = eval('(' + data + ')');
					if (json.success) {
						$("#shareresourcesdialog").hide();
						$("#dialogframe").hide();
						$("#overlay").hide();
						update_shares();
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
	var env = parseInt($("#environment").val());
	if ($("#getresourcesdialog .warning")) {
	    $("#getresourcesdialog .warning").remove();
	}
	$.post("../control/ajax_getvessels",
			{ num: numvessels, env: env },
			function (data) {
				var json = eval('(' + data + ')');
				// alert(json.mypercent);
				// alert(json.success);
				if (json.success) {
					$("#getresourcesdialog").hide();
					$("#dialogframe").hide();
					$("#overlay").hide();
					update_shares();
				} else {
					create_warning(json.error, $("#getresourcesdialog h3"));
				}
			});
}

/*
	Create and insert a warning sign after the given position
*/

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


function update_credits() {
	$.post("../control/ajax_getcredits",
			function (data) {
				$("#credits").empty();
				$("#creditnames").empty();
				$("#creditotherstable tr:gt(0)").empty();
				var json = eval('(' + data + ')');
				var total_others = 0;
				for (var i = 0; i < json[0].length; i++) {
					add_cell("credits", json[0][i].username, json[0][i].percent);
				}
				for (var i = 0; i < json[1].length; i++) {
					add_other("credits", json[1][i].username, json[1][i].percent);
					total_others += json[1][i].percent;
				}
				if (total_others > 0) {
					add_cell("credits", "Others", total_others);
				}
				add_cell("credits", json[2][0].username, json[2][0].percent);
				$("#vesselscredits").text(json[3] + " vessels credits");
				$("#creditotherstable tr:odd").addClass("odd");
				$("#creditotherstable tr:even").addClass("even");
			}, 
			"json");
}

function update_shares() {
	$.post("../control/ajax_getshares",
			function (data) {
				$("#usage").empty();
				$("#usagenames").empty();
				$("#usageotherstable tr:gt(0)").empty();
				var json = eval('(' + data + ')');
				var total_percent = 0;
				var total_others = 0;
				for (var i = 0; i < json[0].length; i++) {
					add_cell("shares", json[0][i].username, json[0][i].percent);
					total_percent += json[0][i].percent;
				}
				for (var i = 0; i < json[1].length; i++) {
					add_other("shares", json[1][i].username, json[1][i].percent);
					total_others += json[1][i].percent;
				}
				total_percent += total_others + json[2][0].percent;
				if (total_others > 0) {
					add_cell("shares", "Others", total_others);
				}
				add_cell("shares", json[2][0].username, json[2][0].percent);
				add_cell("shares", "Free", 100 - total_percent);
				$("#vesselsavailable").text(json[3] + " vessels available");
				update_numvessels(json[3]);
				$("#usageotherstable tr:odd").addClass("odd");
				$("#usageotherstable tr:even").addClass("even");
			},
			"json");
}


function add_cell(type, username, percent) {
	if (type == "credits") {
		var block = create_block(username, percent, false);
		var label = create_label(username, percent, false);
		$("#credits").append(block);
		$("#creditnames").append(label);
	} else if (type == "shares") {
		var block = create_block(username, percent, true);
		var label = create_label(username, percent, true);
		$("#usage").append(block);
		$("#usagenames").append(label);
	}
}


function update_numvessels(number) {
	$("#numvessels").empty();
	for (var i = 1; i <= number; i++) {
		var option = $(document.createElement("option"));
		option.val(i);
		option.text(i);
		$("#numvessels").append(option);
	}
}
