"""
Sample script showing how to do remote port forwarding over paramiko.
This script connects to the requested SSH server and sets up remote port
forwarding (the openssh -R option) from a remote port through a tunneled
connection to a destination reachable from the local machine.
"""

import getpass
import os
import socket
import select
import sys
import threading
from optparse import OptionParser
import paramiko


def handler(chan, host, port):
    sock = socket.socket()
    try:
        sock.connect((host, port))
    except Exception as e:
        print("Forwarding request to %s:%d failed: %r" % (host, port, e))
        return

    print(
        "Connected!  Tunnel open %r -> %r -> %r"
        % (chan.origin_addr, chan.getpeername(), (host, port))
    )
    while True:
        r, w, x = select.select([sock, chan], [], [])
        if sock in r:
            data = sock.recv(1024)
            if len(data) == 0:
                break
            chan.send(data)
        if chan in r:
            data = chan.recv(1024)
            if len(data) == 0:
                break
            sock.send(data)
    chan.close()
    sock.close()
    print("Tunnel closed from %r" % (chan.origin_addr,))


def reverse_forward_tunnel(server_port, remote_host, remote_port, transport):
    transport.request_port_forward("", server_port)
    while True:
        chan = transport.accept(1000)
        if chan is None:
            continue
        thr = threading.Thread(
            target=handler, args=(chan, remote_host, remote_port)
        )
        thr.setDaemon(True)
        thr.start()


def main(username, listen_port, server, vnc_port, keyfile):
    look_for_keys = True
    remote = ['localhost', vnc_port]
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.WarningPolicy())

    print("Connecting to ssh host %s:%d ..." % (server[0], server[1]))
    try:
        client.connect(
            server[0],
            server[1],
            username=username,
            key_filename=keyfile,
            look_for_keys=look_for_keys,
            password=None,
        )
    except Exception as e:
        print("*** Failed to connect to %s:%d: %r" % (server[0], server[1], e))
        sys.exit(1)

    print(
        "Now forwarding remote port %d to %s:%d ..."
        % (listen_port, remote[0], remote[1])
    )

    try:
        reverse_forward_tunnel(
            listen_port, remote[0], remote[1], client.get_transport()
        )
    except KeyboardInterrupt:
        print("C-c: Port forwarding stopped.")
        sys.exit(0)


if __name__ == "__main__":
    from usystem.pystunnel import Stunnel
    import platform
    import time
    if platform.system() == 'Windows':
        appdata = os.getenv('APPDATA')
        app_dir = os.path.join(appdata, 'usystem')
        if not os.path.exists(app_dir):
            os.mkdir(app_dir)
        stunnel_path = os.path.join(app_dir, 'stunnel')
        if not os.path.exists(os.path.join(app_dir, 'stunnel')):
            os.mkdir(os.path.join(app_dir, 'stunnel'))
        vnc_server = 'C:\\Program Files\\USystem\\UConnect\\tvnserver.exe'
        stunnel_server = 'C:\\Program Files\\USystem\\stunnel\\bin\\tstunnel.exe'
    elif platform.system() == 'Linux':
        appdata = os.path.expanduser("~")
        app_dir = os.path.join(appdata, '.usystem')
        if not os.path.exists(app_dir):
            os.mkdir(app_dir)
        stunnel_path = os.path.join(app_dir, 'stunnel')
        if not os.path.exists(os.path.join(app_dir, 'stunnel')):
            os.mkdir(os.path.join(app_dir, 'stunnel'))
        vnc_server = '/opt/usystem/uconnect'
        stunnel_server = 'stunnel'
    elif platform.system() == 'Darwin':
        appdata = os.path.expanduser("~")
        app_dir = os.path.join(appdata, '.usystem')
        if not os.path.exists(app_dir):
            os.mkdir(app_dir)
        stunnel_path = os.path.join(app_dir, 'stunnel')
        if not os.path.exists(os.path.join(app_dir, 'stunnel')):
            os.mkdir(os.path.join(app_dir, 'stunnel'))
        vnc_server = None
        stunnel_server = None
    else:
        print("Unknown platform")
        sys.exit(0)

    #TODO: AUTOMATIC DOWNLOAD CA.pem, minion.pem
    #TODO: get from DB remote_port

    stun_data = "debug = 7\n\
        output = {2}\n\
        [vnc]\n\
        CAfile = {0}\n\
        accept  = 127.0.0.1:5900\n\
        connect = 127.0.0.1:5899\n\
        key = {1}\n\
        cert = {1}\n" \
        .format(os.path.join(stunnel_path, 'cacert.pem'), os.path.join(stunnel_path, 'minion.pem'),
                os.path.join(stunnel_path, 'stun.log'))
    stunnel = Stunnel(os.path.join(stunnel_path, 'stunnel.conf'), stun_data)
    rc = stunnel.start(stunnel_server)
    time.sleep(2)
    if rc.pid:
        remote_port = 5934
        keyfile = os.path.join(app_dir, 'stun_rsa.key')
        main('stun', remote_port, ['91.216.187.11', 22], 5900, keyfile)
    else:
        print("Unable to start TLS")
        sys.exit(0)