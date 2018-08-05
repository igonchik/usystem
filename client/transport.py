#!/usr/bin/python
# -*- coding: utf-8 -*-

import time
import aiohttp
import asyncio
import os
import ssl
from client.client_func import USystem

USYSTEM_VERSION = '0.1.0'


class UTransport:
    def __init__(self, remote_ip=None, cert=None, cacert=None, remote_port=None, usystem_context=True):
        self.send_ping_error_count = 0
        self.usystem_context = usystem_context
        if usystem_context:
            self.usysapp = USystem()
        self.send_ping_flag = True
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
            cert = self.usysapp.cert
        if usystem_context:
            cacert = self.usysapp.cacert
        self.sslcontext = ssl.create_default_context(cafile=cacert)
        self.sslcontext.load_cert_chain(cert)
        self.ping_task = asyncio.Task(self.send_ping())
        self.ping_loop = asyncio.get_event_loop()

    def thread_transport(self):
        try:
            self.ping_loop.run_until_complete(self.ping_task)
        except asyncio.CancelledError:
            pass

    async def send_task_response(self, task):
        """
        :param task: [[task_id, status_id], [task_id, status_id]]
        :return: sended boolean
        """
        sended = False
        sended_count = 0
        while not sended or sended_count <= 5:
            ssl_connection = aiohttp.TCPConnector(ssl=self.sslcontext)
            async with aiohttp.ClientSession(connector=ssl_connection) as session:
                try:
                    async with session.post('https://{0}:{1}/'.format(self.remote_ip, self.remote_port),
                                            json={'version': self.version, 'task': task}, timeout=5) as response:
                        if response.status == 200:
                            await response.json()
                            sended = True
                        else:
                            sended_count += 1
                            print('Can not read response')
                            time.sleep(5)
                except:
                    sended_count += 1
                    print('Find exception in ping request')
                    time.sleep(5)
        return sended

    async def send_ping(self):
        while self.send_ping_flag:
            ssl_connection = aiohttp.TCPConnector(ssl=self.sslcontext)
            async with aiohttp.ClientSession(connector=ssl_connection) as session:
                try:
                    async with session.post('https://{0}:{1}/'.format(self.remote_ip, self.remote_port),
                                            json={'version': self.version}, timeout=5) as response:
                        if response.status == 200:
                            self._parse_task_response(await response.json())
                            self.send_ping_error_count = 0
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
        if self.usystem_context and 'vnc' in response.keys():
            self.usysapp.run_tun(int(response['vnc'][1]))
        elif self.usystem_context and 'certfile' in response.keys():
            self.usysapp.update_certs(cert=response['certfile'][1])
        elif self.usystem_context and 'cacertfile' in response.keys():
            self.usysapp.update_certs(cacert=response['cacertfile'][1])


if __name__ == '__main__':
    import _thread
    app = UTransport('usystem.com',
                     os.path.join(os.path.dirname(os.path.abspath(__file__)), 'testcerts', 'minion.pem'),
                     os.path.join(os.path.dirname(os.path.abspath(__file__)), 'testcerts', 'cacert3.pem'),
                     8080, usystem_context=False)
    _thread.start_new_thread(app.thread_transport, ())
    while True:
        pass
