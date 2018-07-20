adduser uadmin

/etc/hosts usystem_srv <ip>

#for websock
apt-get install python3-mox3
apt-get install python3-nose
apt-get install python3-numpy

#for salt
apt-get install python-jinja2
apt-get install python-msgpack
apt-get install libzmq3-dev cython
apt-get install swig
/opt/work/pyzmq-master/setup.py build
/opt/work/pyzmq-master/setup.py install
/opt/work/m2crypto-master/setup.py build
/opt/work/m2crypto-master/setup.py install


mkdir /var/log/usystem/
mkdir -p /etc/usystem/pki/
chown -R uadmin /var/log/usystem/
chown -R uadmin /etc/usystem/
mkdir /var/cache/usystem
chown uadmin /var/cache/usystem
mkdir /var/run/usystem
chown uadmin /var/run/usystem/
