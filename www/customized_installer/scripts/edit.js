var total = 0;
var add;
var lastid;

window.onload = function() {
	createAdd();
	createElement();
};

//Creates the add button

function createAdd() {
	add = document.createElement("li");
	add.textContent = "Add";
	add.id = "add";
	add.onclick = createElement;
	add.display = "none";
	$("users").appendChild(add);  
	new Effect.Appear(add.id);
}

//Creates a new list element

function createElement() {
	total++;
	$("users").removeChild(add);
	var user = document.createElement("li");
	user.display = "none";
	user.id = "user" + total;
	user.className = "user";
	var name = document.createElement("input");
	name.id = "name" + total;
	name.className = "name";
	name.textContent = "Username";
	name.type = "text";
	name.name = "username"
	var pubkey = document.createElement("input");
	pubkey.id = "pubkey" + total;
	pubkey.className = "pubkey";
	pubkey.type = "file";
	pubkey.name = "public";
	var privkey = document.createElement("span");
	var remove = document.createElement("span");
	remove.textContent = "X";
	remove.className = "remove";
	remove.onclick = removeElement;
	user.appendChild(name);
	user.appendChild(pubkey);
	user.appendChild(privkey);
	user.appendChild(remove);
	$("users").appendChild(user);
	new Effect.SlideDown(user.id);
	createAdd();
}

//Fades a list Element
function removeElement() {
	lastId = this.parentNode.id;
	total--;
	new Effect.Fade(lastId, 
		{afterFinish: remove
		}
	);
}

//Removes the faded element
function remove() {
	$("users").removeChild($(lastId));
	reorder();
}

//Renames the Ids (so they always go user1, user2, etc)
function reorder() {
	var users = $$(".user");
	var names = $$(".name");
	var publickeys = $$(".pubkey");
	for (var i = 0;i < users.length;i++) {
		users[i].id = "user" + (i+1);
	}
	for (var j = 0;j < names.length;j++) {
		names[j].id = "name" + (j+1);
	}
	for (var k = 0;k < publickeys.length;k++) {
		publickeys[k].id = "pubkey" + (k+1);
	}
}
