#!/bin/bash

# This legacy script pre-dates the salt-bootstrap project. In most cases, the
# bootstrap-salt.sh script is the recommended script for installing salt onto
# a new minion. However, that may not be appropriate for all situations. This
# script remains to help fill those needs, and to provide an example for users
# needing to write their own deploy scripts.

mkdir -p /etc/usystem/pki
echo '{{ vm['priv_key'] }}' > /etc/usystem/pki/minion.pem
echo '{{ vm['pub_key'] }}' > /etc/usystem/pki/minion.pub
cat > /etc/usystem/minion <<EOF
{{minion}}
EOF

# add-apt-repository requires an additional dep and is in different packages
# on different systems. Although seemingly ubiquitous it is not a standard,
# and is only a convenience script intended to accomplish the below two steps
# doing it this way is universal across all debian and ubuntu systems.
echo deb http://ppa.launchpad.net/saltstack/usystem/ubuntu `lsb_release -sc` main | tee /etc/apt/sources.list.d/saltstack.list
wget -q -O- "http://keyserver.ubuntu.com:11371/pks/lookup?op=get&search=0x4759FA960E27C0A6" | apt-key add -

apt-get update
apt-get install -y -o DPkg::Options::=--force-confold salt-minion

# minion will be started automatically by install
