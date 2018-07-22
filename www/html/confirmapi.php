<?php
$dbconn = pg_connect('dbname=usystem');
$query = 'update usystem_pubuser set username = \'t\' where username = \''.htmlspecialchars($_GET['uname']).'\';';
pg_query($dbconn, $query);
$query = 'insert into usystem_pubworker (username) values(\''.$_GET['uname'].'\');';
if (pg_query($dbconn, $query)) {
?>
<a href="/">Successful!</a>
<?php
} else
{
	echo 'Ooops';
die('Could not connect: ' . pg_last_error());
}
pg_free_result($result);
pg_close($dbconn);
?>

