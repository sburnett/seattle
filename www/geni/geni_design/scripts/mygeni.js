
$(document).ready(function() {
    // load();
	var credits = $("#credits");
	var creditnames = $("#creditnames");
	create_block(credits, "Me", 35, false);
	create_block(credits, "Ivan", 25, false);
	create_block(credits, "Justin", 15, false);
	create_block(credits, "Sean", 10, false);
	create_block(credits, "Others", 15, false);
	
	create_label(creditnames, "Me", 35);
	create_label(creditnames, "Ivan", 25);
	create_label(creditnames, "Justin", 15);
	create_label(creditnames, "Sean", 10);
	create_label(creditnames, "Others", 15);
	
	var usage = $("#usage");
	var usagenames = $("#usagenames");
	create_block(usage, "Justin", 15, true);
	create_block(usage, "Others", 20, true);
	create_block(usage, "Me", 30, true);
	create_block(usage, "Free", 35, true);
	create_label(usagenames, "Justin", 15);
	create_label(usagenames, "Others", 20);
	create_label(usagenames, "Me",30);
	create_label(usagenames, "Free", 35);
	
	$("#getresourcesbutton").click(get_resources_dialog);
	$("#getresourcesdialog button").click(close_dialog);
	
});


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
		if (username == "Free") {
			block.attr("id", "free");
			
			var get = $(document.createElement('a'));
			get.attr('id','getresourcesbutton');
			get.attr('href','#');
			get.text('get');
			block.append(get);
			
			var share = $(document.createElement('a'));
			share.attr('id','shareresources');
			share.attr('href','#');
			share.text('share');
			block.append(share);
			
		} else if (username != "Me" && username != "Others" ) {
			var close = $(document.createElement('a'));
			close.attr('href','#');
			close.text('x');
			close.click(remove_block);
			block.append(close);
			// percent.click(change_percent);
			
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
	actual width
*/
function edit_block(block, width) {
	$(block).children("span").text(width + '%');
	block.css("width", width + '%');
}


/*
	Remove the block from the usage bar and resize free block to
	fit the width of the bar
*/
function remove_block() {
	var removed_percent = parseInt($(this).next().text());
	$(this).parent().remove();
	var free_percent = parseInt($("#free span").text());
	edit_block($("#free"), free_percent + removed_percent);
}

/*
	Create a name label with given width and append it to
	the given name table.
*/

function create_label(names, username, width) {
	var label = $(document.createElement('td'));
	label.text(username);
	label.css({
		'width': width + '%'
	});
	names.append(label);
}

function change_percent() {
	$(this).attr("id", "percent");
	
	var input = $(document.createElement("input"));
	input.attr("type", "text");
	input.attr("id", "percent_input");
	input.blur(save_percent);
	// var save = $(document.createElement("button"));
	// save.text("save");
	// save.click(save_percent);

	$(this).empty();
	$(this).append(input);
	$(this).append(' % ');
	// $(this).append(save);	
}

function save_percent() {
	var percent_input = $("#percent_input").val();
	var new_percent = $(document.createElement('span'));
	new_percent.text(percent_input + '%');
	new_percent.click(change_percent);
	$("#percent").replaceWith(new_percent);
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
	$("#dialogframe").fadeIn("slow");
	$("#overlay").fadeIn("slow");
}

function close_dialog() {
	$(this).parent().parent().hide();
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
	$.get("data.txt", 
		function (data) {
			update_blocks(data);
		}
	);
}

function update_blocks() {
	
}
