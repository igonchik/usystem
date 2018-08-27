#!/bin/bash

echo '' > /home/cacert.pem
for d in /home/*/ ; do
    if [ -f "$d"cacert.pem ]; then
        cat "$d"cacert.pem "$d"cacrl.pem >> /home/cacert.pem || true
    fi
done

kill `ps -ef | grep HttpsServer.py | grep python | awk '{print $2}'`
kill `ps -ef | grep KeyCreator.py | grep python | awk '{print $2}'`
/usr/local/django/usystem/ctaskserver/KeyCreator.py > /var/log/usystem/keyserver.log &
/usr/local/django/usystem/ctaskserver/HttpsServer.py > /var/log/usystem/httsserver.log &
