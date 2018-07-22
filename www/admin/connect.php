<?php
$dbconn = pg_connect('dbname=usystem user='.$_SERVER['PHP_AUTH_USER'].'');

?>
USER='test1'
portnum=`netstat -luntp | awk '{print $4}' | cut -d ':' -f2 | sort -k 1 -g | tail -n 1`
portnum=$((portnum+1))
python3 /var/www/umaster/websockify/run --web /var/www/umaster/websockify/templates/ 192.168.233.11:$portnum 192.168.133.85:5901 --verify-client --timeout 10 --ssl-version tlsv1_2 --cert /home/$USER/p12/web.p12 --ssl-only --cafile /home/$USER/cacert.pem --auth-plugin ClientCertCNAuth --auth-source test1
