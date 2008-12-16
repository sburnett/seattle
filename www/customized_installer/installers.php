<?php
session_start();
$mypid = session_id();
?>

<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN"
"http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">

<!--
Installer download Page for Customized Installer
-->


	<head>
		<title>Download Installers</title>
		<link rel="stylesheet" type="text/css" href="style.css" />
		<script src="scripts/prototype.js" type="text/javascript"></script>
		<script src="scripts/installers.js" type="text/javascript"></script>
	</head>

	<body>
		<div id="content"> 
			<h1 id="header"> Download your installers </h1>
			
			<p class="comment">
				<a href="download/<?php echo $mypid ?>/public.zip" target="_blank"> Download all public keys </a>&nbsp;&nbsp;
				<a href="download/<?php echo $mypid ?>/private.zip" target="_blank"> Download all private keys </a>
			</p>
			<p class="comment"> Below you will find the installer links for the GENI distributed system </p>
			<p class="comment"> (Click on the image to download your installer)</p>
			<table id="installers">
				<colgroup>
					<col id="win" /><col id="mac" /><col id="linux" />
				</colgroup>
				<tr> 
					<td> <a href="download/<?php echo $mypid ?>/seattle_win.zip" target="_blank"> <img src="images/win.jpg" alt="Windows" /> </a> </td>
					<td> <a href="download/<?php echo $mypid ?>/seattle_mac.tgz" target="_blank"> <img src="images/osx.jpg" alt="Mac" /> </a> </td>
					<td> <a href="download/<?php echo $mypid ?>/seattle_linux.tgz" target="_blank"> <img src="images/linux.jpg" alt="Linux" /> </a> </td>
				</tr>
				<tr id="os">
					<td> Windows </td>
					<td> Mac </td>
					<td> Linux </td>
				</tr>
				<tr id="instruction"> 
					<td>
						<p>Instructions:</p>
						<ol>
							<li>Download the Seattle zip file to your computer</li>
					   		<li>Extract the zip file to the directory in which you would like to install Seattle.</li>
							<li>Double click (or run from the command line) install.bat.</li>
						</ol>
						<br />
						To check that Seattle is running, look in Task Manager for the process pythonw.exe.
					</td> 
					<td>
						<p>Instructions:</p>
						(Note: You must have Python 2.5 installed)
						<br /><br />
						<ol>
							<li>Download the Seattle tarball to your computer</li>
						   	<li>Extract the tarball to the directory in which you would like to install Seattle.</li>
							<li>Navigate to that directory and run ./install.sh (or python install.py).</li>
						</ol>
						<br />
						To check that Seattle is running, try running: ps Aww | grep nmmain.py | grep -v grep
					</td> 
					<td>
						<p>Instructions:</p>
						(Note: You must have Python 2.5 installed)
						<br /><br />
						<ol>
							<li>Download the Seattle tarball to your computer</li>
						   	<li>Extract the tarball to the directory in which you would like to install Seattle.</li>
							<li>Navigate to that directory and run ./install.sh (or python install.py).</li>
						</ol>
						<br />
						To check that Seattle is running, try running: ps -f | grep nmmain.py | grep -v grep
					</td> 
				</tr>
			</table>
	</body>
</html>
