#!/usr/bin/python
# -*- coding: utf-8 -*-

# TODO: Disable crypto in paramiko and sshd linux
# patch ﻿C:\Users\ds-goncharov\AppData\Local\Programs\Python\Python37\Lib\subprocesses.py 1193 try:except:return 0

import platform
import os
from time import sleep
import subprocess
from client.pystunnel import Stunnel
import socket
import select
import paramiko
import _thread
import psutil
import configparser
import sys


class USystem:
    def _read_config(self):
        config = configparser.ConfigParser()
        if os.path.isfile(os.path.join(self.app_dir, 'usystem.ini')):
            config.read(os.path.join(self.app_dir, 'usystem.ini'))
            if 'usystem' in config:
                try:
                    self.remote_ip = config['usystem']['remote_ip']
                    self.local_port = int(config['usystem']['local_port'])
                    self.vnc_port = int(config['usystem']['vnc_port'])
                    self.remote_sshport = int(config['usystem']['remote_sshport'])
                    self.cacert = config['usystem']['cacert_path']
                    self.cert = config['usystem']['cert_path']
                    self.policy = int(config['usystem']['policy'])
                    self.transport_port = int(config['usystem']['transport_port'])
                except:
                    print('USystem app is not configurated! exit...')
                    return False
        return True

    def __init__(self):
        self.stopFlag = True
        self.remote_ip = None
        self.remote_sshport = None
        self.local_port = None
        self.vnc_port = None
        self.cacert = None
        self.cert = None
        self.transport_port = 0
        self.app_error = True
        self.task_error = list()
        self.policy = 0
        self.vnc_connect = False

        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        if platform.system() == 'Windows':
            appdata = os.getenv('APPDATA')
            self.app_dir = os.path.join(appdata, 'usystem')
            if not os.path.exists(self.app_dir):
                os.mkdir(self.app_dir)
            self.stunnel_path = os.path.join(self.app_dir, 'stunnel')
            if not os.path.exists(os.path.join(self.app_dir, 'stunnel')):
                os.mkdir(os.path.join(self.app_dir, 'stunnel'))
            self.vnc_server = 'C:\\Program Files\\USystem\\UConnect\\tvnserver.exe'
            self.stunnel_server = 'C:\\Program Files\\USystem\\stunnel\\bin\\tstunnel.exe'
            self.app_error = self._read_config()
            self._configure_tunnel()
            self._reconfigure_vnc_win_reg()
        elif platform.system() == 'Linux':
            appdata = os.path.expanduser("~")
            self.app_dir = os.path.join(appdata, '.usystem')
            if not os.path.exists(self.app_dir):
                os.mkdir(self.app_dir)
            self.stunnel_path = os.path.join(self.app_dir, 'stunnel')
            if not os.path.exists(os.path.join(self.app_dir, 'stunnel')):
                os.mkdir(os.path.join(self.app_dir, 'stunnel'))
            self.vnc_server = '/opt/usystem/uconnect'
            self.stunnel_server = 'stunnel'
            self.app_error = self._read_config()
            self._configure_tunnel()
            self._reconfigure_vnc_unix()
        else:
            print("Unknown platform")
            self.vnc_server = None
            self.stunnel_server = None
            self.app_dir = None
            self.tunnel = None
            self.cacert = None
            self.cert = None
            self.app_error = False

    def close(self):
        self._kill_tunnel()
        self._kill_vnc()

    @staticmethod
    def _reconfigure_vnc_win_reg():
        import winreg
        subkey = "Software\\TightVNC\\Server"
        hKey = winreg.CreateKey(winreg.HKEY_CURRENT_USER, subkey)
        winreg.SetValueEx(hKey, "ExtraPorts", 0, winreg.REG_SZ, "")
        winreg.SetValueEx(hKey, "QueryTimeout", 0, winreg.REG_DWORD, 0x0000001e)
        winreg.SetValueEx(hKey, "QueryAcceptOnTimeout", 0, winreg.REG_DWORD, 0x00000000)
        winreg.SetValueEx(hKey, "LocalInputPriorityTimeout", 0, winreg.REG_DWORD, 0x00000003)
        winreg.SetValueEx(hKey, "LocalInputPriority", 0, winreg.REG_DWORD, 0x00000000)
        winreg.SetValueEx(hKey, "BlockRemoteInput", 0, winreg.REG_DWORD, 0x00000000)
        winreg.SetValueEx(hKey, "BlockLocalInput", 0, winreg.REG_DWORD, 0x00000000)
        winreg.SetValueEx(hKey, "IpAccessControl", 0, winreg.REG_SZ, "")
        winreg.SetValueEx(hKey, "RfbPort", 0, winreg.REG_DWORD, 0x0000170b)
        winreg.SetValueEx(hKey, "HttpPort", 0, winreg.REG_DWORD, 0x000016a8)
        winreg.SetValueEx(hKey, "DisconnectAction", 0, winreg.REG_DWORD, 0x00000000)
        winreg.SetValueEx(hKey, "AcceptRfbConnections", 0, winreg.REG_DWORD, 0x00000001)
        winreg.SetValueEx(hKey, "UseVncAuthentication", 0, winreg.REG_DWORD, 0x00000000)
        winreg.SetValueEx(hKey, "UseControlAuthentication", 0, winreg.REG_DWORD, 0x00000000)
        winreg.SetValueEx(hKey, "RepeatControlAuthentication", 0, winreg.REG_DWORD, 0x00000000)
        winreg.SetValueEx(hKey, "LoopbackOnly", 0, winreg.REG_DWORD, 0x00000001)
        winreg.SetValueEx(hKey, "AcceptHttpConnections", 0, winreg.REG_DWORD, 0x00000000)
        winreg.SetValueEx(hKey, "LogLevel", 0, winreg.REG_DWORD, 0x00000000)
        winreg.SetValueEx(hKey, "EnableFileTransfers", 0, winreg.REG_DWORD, 0x00000001)
        winreg.SetValueEx(hKey, "RemoveWallpaper", 0, winreg.REG_DWORD, 0x00000001)
        winreg.SetValueEx(hKey, "UseMirrorDriver", 0, winreg.REG_DWORD, 0x00000001)
        winreg.SetValueEx(hKey, "EnableUrlParams", 0, winreg.REG_DWORD, 0x00000001)
        winreg.SetValueEx(hKey, "AlwaysShared", 0, winreg.REG_DWORD, 0x00000000)
        winreg.SetValueEx(hKey, "NeverShared", 0, winreg.REG_DWORD, 0x00000000)
        winreg.SetValueEx(hKey, "DisconnectClients", 0, winreg.REG_DWORD, 0x00000001)
        winreg.SetValueEx(hKey, "PollingInterval", 0, winreg.REG_DWORD, 0x000003e8)
        winreg.SetValueEx(hKey, "AllowLoopback", 0, winreg.REG_DWORD, 0x00000001)
        winreg.SetValueEx(hKey, "VideoRecognitionInterval", 0, winreg.REG_DWORD, 0x00000bb8)
        winreg.SetValueEx(hKey, "GrabTransparentWindows", 0, winreg.REG_DWORD, 0x00000001)
        winreg.SetValueEx(hKey, "SaveLogToAllUsersPath", 0, winreg.REG_DWORD, 0x00000000)
        winreg.SetValueEx(hKey, "RunControlInterface", 0, winreg.REG_DWORD, 0x00000000)
        winreg.SetValueEx(hKey, "IdleTimeout", 0, winreg.REG_DWORD, 0x00000000)
        winreg.SetValueEx(hKey, "VideoClasses", 0, winreg.REG_SZ, "")
        winreg.SetValueEx(hKey, "VideoRects", 0, winreg.REG_SZ, "")

    @staticmethod
    def _reconfigure_vnc_unix():
        # TODO find TightVNC conf
        pass

    def update_certs(self, cert=None, cacert=None):
        import OpenSSL.crypto as crypto
        to = None
        src = None
        error = False
        x509 = None
        if cert:
            to = self.cert
            src = cert
            print("Updating cert file...")
            if os.path.isfile(self.cert):
                old_cert = open(self.cert, 'rt').read()
                try:
                    x509 = crypto.load_certificate(crypto.FILETYPE_PEM, old_cert)
                except:
                    pass
        elif cacert:
            to = self.cacert
            src = cacert
            print("Updating cacert file...")
        if cert or cacert:
            dest = os.open(to, os.O_RDWR | os.O_CREAT)
            try:
                x509_new = crypto.load_certificate(crypto.FILETYPE_PEM, src)
                if x509 and cert:
                    if x509.get_subject().CN == x509_new.get_subject().CN:
                        os.write(dest, cert.encode('utf8'))
                    else:
                        print("Can not change username from {0} to {1}...".format(x509.get_subject().CN,
                                                                                  x509_new.get_subject().CN))
                        error = True
                elif cacert or not x509:
                    os.write(dest, src.encode('utf8'))
            except:
                print("Unable to update cert file...")
                error = True
            finally:
                os.close(dest)

        return error

    def _configure_tunnel(self):
        stun_data = "debug = 7\n" \
                    "output = {2}\n" \
                    "[vnc]\n" \
                    "verify = 2\n" \
                    "sslVersion = TLSv1\n" \
                    "CAfile = {0}\n" \
                    "accept  = 127.0.0.1:{3}\n" \
                    "connect = 127.0.0.1:{4}\n" \
                    "key = {1}\n" \
                    "cert = {1}\n"\
            .format(self.cacert, self.cert,
                    os.path.join(self.stunnel_path, 'stun.log'), self.local_port, self.vnc_port)
        self.tunnel = Stunnel(os.path.join(self.stunnel_path, 'stunnel.conf'), stun_data)

    @staticmethod
    def find_procs_by_name(name):
        """
        Return a list of processes matching 'name'
        """
        assert name, name
        ls = []
        for p in psutil.process_iter():
            name_, exe, cmdline = "", "", []
            try:
                name_ = p.name()
                cmdline = p.cmdline()
                exe = p.exe()
            except (psutil.AccessDenied, psutil.ZombieProcess):
                pass
            except psutil.NoSuchProcess:
                continue
            if name == name_ or (len(cmdline) > 0 and cmdline[0] == name) or os.path.basename(exe) == name:
                ls.append(name)
        return ls

    def _kill_tunnel(self):
        if platform.system() == 'Windows':
            if len(self.find_procs_by_name('tstunnel.exe')) > 0:
                try:
                    os.system("taskkill /f /im tstunnel.exe")
                except:
                    pass
        else:
            subprocess.call(['pkill', 'stunnel'])
        sleep(0.5)

    def _kill_vnc(self):
        if platform.system() == 'Windows':
            if len(self.find_procs_by_name('tvnserver.exe')) > 0:
                try:
                    os.system("taskkill /f /im tvnserver.exe")
                except:
                    pass
        else:
            subprocess.call(['pkill', 'uconnect'])
        sleep(0.5)

    def run_tun(self, rport, work_id):
        def handler(chan, host, port):
            sock = socket.socket()
            try:
                sock.connect((host, port))
            except Exception as e:
                self.task_error.append([work_id, 5])
                self._kill_tunnel()
                self._kill_vnc()
                print("Forwarding request to %s:%d failed: %r" % (host, port, e))
                return

            print(
                    "Connected!  Tunnel open %r -> %r -> %r"
                    % (chan.origin_addr, chan.getpeername(), (host, port))
            )
            while not self.stopFlag:
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
            sys.exit()

        def reverse_forward_tunnel(server_port, remote_host, remote_port, transport):
            try:
                transport.request_port_forward("", server_port)
                self.task_error.append([work_id, 4])
                while True:
                    chan = transport.accept(1000)
                    if chan is None:
                        continue
                    handler(chan, remote_host, remote_port)
            except:
                self.task_error.append([work_id, 6])
                self._kill_tunnel()
                self._kill_vnc()
                sys.exit()

        def tunnel(username, listen_port, server, vnc_port, keyfile):
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
                    password='',
                )
            except Exception as e:
                print("*** Failed to connect to %s:%d: %r" % (server[0], server[1], e))
                self.task_error.append([work_id, 5])
                self._kill_tunnel()
                self._kill_vnc()
                sys.exit()

            print(
                    "Now forwarding remote port %d to %s:%d ..."
                    % (listen_port, remote[0], remote[1])
            )

            reverse_forward_tunnel(
                listen_port, remote[0], remote[1], client.get_transport()
            )

        self.stopFlag = True
        self._kill_tunnel()
        self._kill_vnc()
        rc = self.tunnel.start(self.stunnel_server)
        if platform.system() == 'Windows':
            rcvnc = subprocess.Popen([self.vnc_server, '-run'])
        else:
            rcvnc = subprocess.Popen([self.vnc_server])
        if rc and rc.pid and rcvnc and rcvnc.pid:
            keyfile = os.path.join(self.app_dir, 'stun_rsa.key')
            self.stopFlag = False
            _thread.start_new_thread(tunnel, ('stun', rport, [self.remote_ip, self.remote_sshport], self.local_port,
                                              keyfile))
        else:
            print("Unable to start TLS")
            self._kill_tunnel()
            self._kill_vnc()
            self.task_error.append([work_id, 5])


if __name__ == '__main__':
    app = USystem()
    app.run_tun(5930, 0)
