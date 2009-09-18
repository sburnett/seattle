window.onload = function () {  
  $("dl_keys").onclick = dl_keys;
  $("dl_installers").onclick = go_continue;
  
  $("dl_installers").disabled = true;
};


function dl_keys() {
  location.href = "/html/dl_keys";
  $("dl_installers").disabled = false;
};


function go_continue() {
  location.href = "/html/post_install";
};