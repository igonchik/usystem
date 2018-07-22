<?php
$dbconn = pg_connect('dbname=usystem');

$query = 'SELECT * FROM usystem_pubuser;';
$result = pg_query($query);

echo "Уже в системе: <table>\n";
while ($line = pg_fetch_array($result, null, PGSQL_ASSOC)) {
    echo "\t<tr>\n";
    foreach ($line as $col_value) {
        echo "\t\t<td>$col_value</td>\n";
    }
    echo "\t</tr>\n";
}
echo "</table>\n";
?>

<form action="/registrationapi.php" method="post">
 <p>Ваш логин: <input type="text" name="name" /></p>
 <p>Ваш email: <input type="text" name="email" /></p>
 <p><input type="submit" /></p>
</form>

<?php
pg_free_result($result);
pg_close($dbconn);
?>
