


window.onload = function () {
	call();
};

function call() {
	new Ajax.Request("status", 
	{
		method: "get",
		onSuccess: update,
		onFailure: error
	});

}

function update(Ajax) {
	alert(Ajax.responseText);
}

function error() {
	alert("error");
}