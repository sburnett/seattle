<?php
if (isset($_GET['pid'])) {
	$mypid = $_GET['pid'];
}

?>

<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN"
"http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">

<!--
Links Page for Research Project
-->


	<head>
		<title>Installers Download</title>
		<link rel="stylesheet" type="text/css" href="style.css" />
	</head>

	<body>
		<div id="content"> 
			<h1 id="header"> Download your installers </h1>
			<div id="main"> 
				<div id="links">
					<ul>
						<li><a href="download/<?php echo $mypid ?>/seattle_win.zip" title="Windows Installer" target="_blank">Windows Installer</a></li>
						<li><a href="download/<?php echo $mypid ?>/seattle_mac.tgz" title="Mac Installer" target="_blank">Mac OS X Installer</a></li>
						<li><a href="download/<?php echo $mypid ?>/seattle_linux.tgz" title="Linux Installer" target="_blank">Linux Installer</a></li>
					</ul>
				</div>
			</div>
		</div>
	</body>
</html>
