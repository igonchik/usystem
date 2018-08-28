#!/usr/bin/python
# -*- coding: utf-8 -*-

import time
import aiohttp
import asyncio
import os
import ssl
from client.client_func import USystem
import _thread
import platform

USYSTEM_VERSION = '0.1.0'


class UTransport:
    def __init__(self, remote_ip=None, cert=None, cacert=None, remote_port=None, usystem_context=True):
        self.send_ping_error_count = 0
        if platform.system() == 'Windows':
            self.plarform = 'win'
        elif platform.system() == 'Linux':
            self.plarform = 'lin'
        else:
            self.plarform = 'mac'
        self.cacert = cacert
        self.cert = cert
        self.adminpin = False
        self.goout = False
        self.usystem_context = usystem_context
        self.app_error = True
        self.task = list()
        self.policy = 0
        if usystem_context:
            self.usysapp = USystem()
            self.app_error = self.usysapp.app_error
            self.policy = self.usysapp.policy
        self.send_ping_flag = True
        if not usystem_context:
            self.policy = 0
        else:
            self.policy = self.usysapp.policy
        if not usystem_context:
            self.remote_ip = remote_ip
        else:
            self.remote_ip = self.usysapp.remote_ip
        self.version = USYSTEM_VERSION
        if not usystem_context:
            self.remote_port = remote_port
        else:
            self.remote_port = self.usysapp.transport_port
        if usystem_context:
            self.cert = self.usysapp.cert
        if usystem_context:
            self.cacert = self.usysapp.cacert
        self.sslcontext = ssl.create_default_context(cafile=self.cacert)
        try:
            self.sslcontext.load_cert_chain(self.cert)
        except:
            pass
        self.ping_task = asyncio.Task(self.send_ping())
        self.ping_loop = asyncio.get_event_loop()

    def thread_transport(self):
        try:
            self.ping_loop.run_until_complete(self.ping_task)
        except asyncio.CancelledError:
            pass

    async def send_ping(self):
        while self.send_ping_flag:
            ssl_connection = aiohttp.TCPConnector(ssl=self.sslcontext)
            async with aiohttp.ClientSession(connector=ssl_connection) as session:
                try:
                    if self.usystem_context:
                        self.task.extend(self.usysapp.task_error)
                    json_dict = {'version': self.version, 'platform': self.plarform, 'task': self.task,
                                 'policy': self.policy}
                    if self.adminpin:
                        json_dict.update({'adminpin': self.adminpin})
                        self.adminpin = False
                    if self.goout:
                        json_dict.update({'goout': self.goout})
                        self.goout = False
                    async with session.post('https://{0}:{1}/'.format(self.remote_ip,
                                                                      self.remote_port if os.path.isfile(self.cert) else
                                                                      self.remote_port + 1),
                                            json=json_dict, timeout=5) as response:
                        if response.status == 200:
                            self._parse_task_response(await response.json())
                            self.send_ping_error_count = 0
                            if self.usystem_context:
                                self.task = list()
                                self.usysapp.task_error = list()
                        else:
                            print('Client has not OK response')
                            self.send_ping_error_count += 1
                except:
                    self.send_ping_error_count += 1
                    print('Find exception in ping request')
                if self.send_ping_error_count == 5:
                    self.ping_task.cancel()
                    self.send_ping_flag = False
                    print("Closing send_ping task... Can not establish connection to host {0}!".format(self.remote_ip))
                time.sleep(5)

    def _parse_task_response(self, response):
        print(response)
        if self.policy == 0:
            if self.usystem_context and 'vnc' in response.keys():
                self.usysapp.run_tun(int(response['vnc'][1]), int(response['vnc'][0]))
            if self.usystem_context and 'certfile' in response.keys():
                error = self.usysapp.update_certs(cert=response['certfile'][1])
                if error and response['certfile'][0] > 0:
                    self.task.append([response['certfile'][0], 5])
                else:
                    self.sslcontext = ssl.create_default_context(cafile=self.cacert)
                    try:
                        self.sslcontext.load_cert_chain(self.cert)
                    except:
                        pass
            if self.usystem_context and 'rcertfile' in response.keys():
                error = self.usysapp.remove_certs()
                if error and response['certfile'][0] > 0:
                    self.task.append([response['certfile'][0], 5])
                else:
                    self.sslcontext = ssl.create_default_context(cafile=self.cacert)
            if self.usystem_context and 'cacertfile' in response.keys():
                error = self.usysapp.update_certs(cacert=response['cacertfile'][1])
                if error and response['certfile'][0] > 0:
                    self.task.append([response['cacertfile'][0], 5])
                else:
                    self.sslcontext = ssl.create_default_context(cafile=self.cacert)
                    try:
                        self.sslcontext.load_cert_chain(self.cert)
                    except:
                        pass
        elif self.policy == 1:
            pass


if __name__ == '__main__':
    app = UTransport('usystem.com',
                     os.path.join(os.path.dirname(os.path.abspath(__file__)), 'testcerts', 'minion.pem'),
                     os.path.join(os.path.dirname(os.path.abspath(__file__)), 'testcerts', 'cacert3.pem'),
                     8080, usystem_context=False)
    _thread.start_new_thread(app.thread_transport, ())
    while True:
        pass
