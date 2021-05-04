<?php

if(isset($_GET['id'])){
	$cmd = "whois -h 10.10.10.155";
	//craft the cmd
	$cmd = $cmd.' "'.$_GET['id'].'"';
	echo $cmd;
	$var = shell_exec($cmd);
	echo "<pre>";
	var_dump($var);
	echo "</pre>";
}
