<?php
$dbconn = pg_connect('dbname=usystem');
$query = 'SELECT * FROM usystem_pubuser';
$result = pg_query($query) or die('Ошибка запроса: ' . pg_last_error());

echo "Уже в системе: <table>\n";
while ($line = pg_fetch_array($result, null, PGSQL_ASSOC)) {
    echo "\t<tr>\n";
    foreach ($line as $col_value) {
        echo "\t\t<td>$col_value</td>\n";
    }
    echo "\t</tr>\n";
}
echo "</table>\n";

$query = 'insert into usystem_pubuser values(\''.htmlspecialchars($_POST['name']).'\', \''.$_POST['email'].'\');';
echo $query;
if (pg_query($dbconn, $query)) {
	$query = 'SELECT * FROM usystem_pubuser where username like \''.$_POST['name'].'\'';
	$result = pg_query($query) or die('Ошибка запроса: ' . pg_last_error());
	while ($line = pg_fetch_array($result, null, PGSQL_ASSOC)) {
        	$url='/confirmapi.php?uname='.$line['username'];
	}
?>
<a href="<?php echo $url?>">Confirm!</a>
<?php
} else
{
	echo 'Ooops';
}
pg_free_result($result);
pg_close($dbconn);
?>

